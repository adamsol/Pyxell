
module.exports = {
    title: 'Pyxell',
    description: 'Programming language built with simplicity in mind.',
    theme: 'default-prefers-color-scheme',
    themeConfig: {
        repo: 'adamsol/Pyxell',
        nav: [
            { link: '/playground', text: 'Try it online' },
        ],
        sidebar: [
            ['/manual', 'Manual'],
            ['/specification', 'Specification'],
            ['/why-pyxell', 'Why Pyxell?'],
            ['/playground', 'Playground'],
        ],
        displayAllHeaders: true,
        lastUpdated: 'Documentation version',  // see plugins/version.js
        overrideTheme: 'dark',  // FIXME: code snippets are barely legible in the light theme
    },
    markdown: {
        extendMarkdown: md => {
            const prism = require('prismjs');
            const syntax = require('./utils/pyxell-syntax.js');

            prism.languages.pyxell = {
                'comment': { pattern: /#.*|{#[\s\S]*?#}/, greedy: true },
                'boolean': syntax.atom,
                'keyword': syntax.keyword,
                'variable-name': syntax.variable_name,
                'class-name': syntax.type_name,
                'number': syntax.number,
                'string': { pattern: syntax.string, greedy: true },
            };

            md.use(require('markdown-it-prism'), {
                defaultLanguage: 'pyxell',
            });
        },
    },
    plugins: [require('./plugins/version')],
    clientRootMixin: require('path').resolve(__dirname, 'utils/scroll-fix.js'),
    base: '/docs/',
};
