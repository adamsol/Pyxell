
// https://github.com/vuejs/vuepress/issues/2558
module.exports = {
    mounted() {
        if (location.hash && location.hash !== '#') {
            const anchor_location = decodeURIComponent(location.hash);
            const anchor_element = document.querySelector(anchor_location);
            if (anchor_element && anchor_element.offsetTop) {
                window.scrollTo(0, anchor_element.offsetTop);
            }
        }
    },
};
