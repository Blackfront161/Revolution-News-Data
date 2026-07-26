'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const app = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
const summary = fs.readFileSync(path.join(root, 'article-summary.js'), 'utf8');
const summaryStyles = fs.readFileSync(path.join(root, 'article-summary.css'), 'utf8');
const actions = fs.readFileSync(path.join(root, 'article-actions.js'), 'utf8');
const audio = fs.readFileSync(path.join(root, 'audio-hub.js'), 'utf8');
const styles = fs.readFileSync(path.join(root, 'styles.css'), 'utf8');
const lexicon = fs.readFileSync(path.join(root, 'lexicon-tab.js'), 'utf8');

const orderSource = app.match(
  /function articlePublisherKey\(article\)[\s\S]*?window\.WRNFeedOrder = Object\.freeze\(\{[\s\S]*?\}\);/
);
assert(orderSource, 'Publisher mixing implementation is missing.');
const feedOrder = new Function(
  `const window = {};\n${orderSource[0]}\nreturn { interleaveArticlesByPublisher };`
)();

const input = [
  { quelleName: 'A', id: 1 },
  { quelleName: 'A', id: 2 },
  { quelleName: 'B', id: 3 },
  { quelleName: 'C', id: 4 },
  { quelleName: 'A', id: 5 }
];
const mixed = feedOrder.interleaveArticlesByPublisher(input);
assert.strictEqual(mixed.length, input.length, 'Mixing must not remove articles.');
assert.deepStrictEqual(
  [...mixed].map(item => item.id).sort((a, b) => a - b),
  input.map(item => item.id).sort((a, b) => a - b),
  'Mixing must preserve every article.'
);
for (let index = 1; index < mixed.length; index += 1) {
  assert.notStrictEqual(
    mixed[index - 1].quelleName,
    mixed[index].quelleName,
    'Adjacent publishers must differ when enough alternatives exist.'
  );
}

const crowded = [];
for (let index = 0; index < 8; index += 1) {
  crowded.push({ quelleName:'Dominant', id:`d${index}`, title:`Dominant ${index}`, link:`https://dominant.example/${index}` });
}
for (let index = 0; index < 10; index += 1) {
  crowded.push({ quelleName:`Source ${index}`, id:`s${index}`, title:`Other ${index}`, link:`https://source-${index}.example/item` });
}
crowded.push({ quelleName:'Duplicate mirror', id:'duplicate', title:'Duplicate', link:'https://source-1.example/item?utm_source=test' });
const diversified = feedOrder.interleaveArticlesByPublisher(crowded);
assert.equal(
  diversified.slice(0, 10).filter(item => item.quelleName === 'Dominant').length,
  2,
  'The first ten items may contain at most two articles from one publisher.'
);
assert.equal(
  diversified.filter(item => String(item.link).includes('source-1.example/item')).length,
  1,
  'Tracking variants of the same URL must be deduplicated.'
);

for (const marker of [
  "view.id = 'wrn-summary-view'",
  "view.setAttribute('aria-modal', 'true')",
  "document.body.classList.add('wrn-summary-view-open')",
  "view.querySelector('.wrn-summary-back')?.focus"
]) {
  assert(summary.includes(marker), `Missing summary page marker: ${marker}`);
}
assert(summaryStyles.includes('z-index: 14600'), 'Summary page must remain above article detail.');
assert(
  !summary.includes("card.querySelector('.wrn-article-summary-panel')"),
  'Summary controls must not be injected into the article card.'
);
assert(
  actions.includes("'.wrn-detail-actions .button-row, '"),
  'Article action layout must be restricted to the real action toolbar.'
);

for (const marker of [
  "document.body.classList.add('wrn-podcast-options-open')",
  "modal.style.display = 'flex'"
]) {
  assert(audio.includes(marker), `Missing podcast full-screen marker: ${marker}`);
}
assert(styles.includes('z-index: 13990 !important'), 'Podcast options must appear above article detail.');
assert(styles.includes('bottom: 0 !important'), 'Podcast close controls must remain sticky at the bottom.');

for (const marker of [
  'function articleMediaMarkup(',
  'function loadArticleMedia(',
  'image.dataset.src',
  'loadArticleMedia(idNum)'
]) {
  assert(app.includes(marker), `Missing expanded article image marker: ${marker}`);
}

for (const label of [
  "building: 'Im Aufbau'",
  "building: 'Under construction'",
  "building: 'En desarrollo'",
  "building: 'En construction'",
  "building: 'In costruzione'",
  "building: 'Em construção'",
  "building: 'В разработке'",
  "building: 'Υπό ανάπτυξη'",
  "building: 'Yapım aşamasında'"
]) {
  assert(lexicon.includes(label), `Missing lexicon construction label: ${label}`);
}

console.log('Article workspace 1.8.4 contracts: OK');
