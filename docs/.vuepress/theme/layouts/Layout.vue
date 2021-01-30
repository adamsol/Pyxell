
<template>
    <div>
        <ParentLayout />
        <ClientOnly>
            <DarkMode v-slot="{ mode }" default-mode="dark" class="mode-switch">
                Color mode: {{ mode[0].toUpperCase() + mode.slice(1) }}
            </DarkMode>
        </ClientOnly>
    </div>
</template>

<script>
    import ParentLayout from '@parent-theme/layouts/Layout.vue'
    import { DarkMode } from '@vue-a11y/dark-mode';

    export default {
        components: { ParentLayout, DarkMode },
    };
</script>

<style lang="stylus">
    // Dark colors are the default to prevent irritating blinking when the page is reloaded.
    :root
        --text-color: $textColorDark
        --bg-color: $bgColorDark
        --bg-secondary-color: lighten($bgColorDark, 3%)
        --bg-tertiary-color: lighten($bgColorDark, 10%)
        --border-color: $borderColorDark

    html.light-mode
        --text-color: $textColor
        --bg-color: $bgColor
        --bg-secondary-color: darken($bgColor, 3%)
        --bg-tertiary-color: darken($bgColor, 8%)
        --border-color: $borderColor

    html:not(.light-mode) .home *:not(.action-button)
        color: var(--text-color) !important
        border-color: var(--border-color)

    html, body, .navbar, .navbar .site-name, .navbar .links, .navbar .links .nav-link, .search-box input, .sidebar, .sidebar .sidebar-link
        color: var(--text-color)
        background-color: var(--bg-color)

    .navbar, .sidebar, hr, tr, th, td, h2, .page-nav .inner
        border-color: var(--border-color)

    .search-box input
        border-color: grey
        transition: none

    tr:nth-child(even), th
        background-color: var(--bg-secondary-color)

    .page code
        color: var(--text-color)
        background-color: var(--bg-tertiary-color)

    .mode-switch
        position: fixed
        left: 9rem
        top: 0.8rem
        z-index: 1000
        padding: 8px 16px
        font-weight: bold
        border: 1px solid grey !important
        border-radius: 20px
        outline: none
</style>
