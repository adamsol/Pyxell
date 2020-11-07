
const filepath = require('path').resolve(__dirname, '../../../version.txt');
const version = require('fs').readFileSync(filepath).toString();

// A small hack to display the current version in the page footer.
// https://vuepress.vuejs.org/plugin/official/plugin-last-updated.html
module.exports = {
    extendPageData($page) {
        $page.lastUpdated = version;
    },
};
