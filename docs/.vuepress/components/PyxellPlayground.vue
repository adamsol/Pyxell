
<template>
    <div>
        <VueCodemirror v-model="code" ref="code" :options="options" />
        <label title="Standard input for your program.">
            <input v-model="show_input" type="checkbox" />
            Input
        </label>
        <label style="padding-left: 6px" title="Will make compilation slower, but your program may run faster.">
            <input v-model="optimization" type="checkbox" />
            Optimizations
        </label>
        <div class="input" :style="{ 'max-height': show_input ? INPUT_HEIGHT : 0 }">
            <VueCodemirror v-model="input" ref="input" :options="{ mode: null, theme: THEME }" />
        </div>
        <div style="text-align: right">
            <button :disabled="running" class="run" @click="run">
                <span v-if="running" class="spin">
                    &#x25e0;
                </span>
                <span v-else>
                    &#x25B6;
                </span>
                Run
            </button>
        </div>
        <pre :style="{ color: error ? 'red' : 'white' }">{{ output }}</pre>
    </div>
</template>

<script>
    import axios from 'axios';
    import VueCodemirror from 'vue-codemirror/src/codemirror.vue';
    import { CodeMirror } from 'vue-codemirror';
    import 'codemirror/lib/codemirror.css';
    import 'codemirror/theme/dracula.css';
    import 'codemirror/addon/mode/simple.js';

    import syntax from '../utils/pyxell-syntax.js';

    CodeMirror.defineSimpleMode('pyxell', {
        start: [
            { token: 'comment', regex: /#.*/ },
            { token: 'comment', regex: /{#/, next: 'comment' },
            { token: 'variable', regex: /\bprint\b/ },
            { token: 'atom', regex: syntax.atom },
            { token: 'keyword', regex: syntax.keyword },
            { token: 'variable-2', regex: syntax.variable_name },
            { token: 'variable-3', regex: syntax.type_name },
            { token: 'number', regex: syntax.number },
            { token: 'string', regex: syntax.string },
        ],
        comment: [
            { token: 'comment', regex: /.*?#}/, next: 'start' },
            { token: 'comment', regex: /.*/ },
        ],
    });

    export default {
        components: { VueCodemirror },
        data: () => ({
            CODE_HEIGHT: '450px',
            INPUT_HEIGHT: '120px',
            THEME: 'dracula',

            code: '',
            input: '',
            show_input: false,
            optimization: false,
            running: false,
            error: false,
            output: '',
        }),
        computed: {
            options() {
                return {
                    mode: 'pyxell',
                    theme: this.THEME,
                    lineNumbers: true,
                    indentUnit: 4,
                    extraKeys: {
                        'Tab': cm => {
                            if (cm.getMode().name === 'null') {
                                cm.execCommand('insertTab');
                            } else {
                                if (cm.somethingSelected()) {
                                    cm.execCommand('indentMore');
                                } else {
                                    cm.execCommand('insertSoftTab');
                                }
                            }
                        },
                        'Shift-Tab': cm => {
                            cm.execCommand('indentLess');
                        },
                    },
                };
            },
        },
        methods: {
            async run() {
                const input = this.show_input ? this.input : '';
                this.output = '';
                this.running = true;

                localStorage.setItem('code', this.code);
                localStorage.setItem('input', input);

                try {
                    let response = await axios.post('/run/', {
                        code: this.code,
                        input: input,
                        optimization: this.optimization,
                    });
                    this.error = !!response.data.error;
                    this.output = response.data.error || response.data.output;
                }
                catch (error) {
                    this.error = true;
                    this.output = 'Unknown error';
                    throw error;
                }
                finally {
                    this.running = false;
                }
            },
        },
        created() {
            this.code = localStorage.getItem('code') || '\nprint "Hello, world!"\n';
            this.input = localStorage.getItem('input') || '';
            this.show_input = this.input !== '';
        },
        mounted() {
            this.$refs.code.codemirror.setSize('auto', this.CODE_HEIGHT);
            this.$refs.input.codemirror.setSize('auto', this.INPUT_HEIGHT);
        },
    };
</script>

<style lang="stylus">
    .CodeMirror
        border: 1px solid #eee
        box-sizing: border-box

    div.input
        overflow: hidden
        transition: max-height 0.4s

    button.run
        background-color: $accentColor
        border: none
        border-radius: 5px
        color: white
        font-size: 1.2em
        padding: 5px 25px

        &:not(:disabled)
            cursor: pointer

    .spin
        animation: spin 1s linear infinite
        display: inline-block

    @keyframes spin
        from
            transform: rotate(0deg)
        to
            transform: rotate(360deg)
</style>
