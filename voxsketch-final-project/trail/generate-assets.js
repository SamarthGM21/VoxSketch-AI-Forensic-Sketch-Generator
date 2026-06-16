// This is a helper script to run on your computer.
// It will scan your image folders and print the 'featureAssets' object for you.
const fs = require('fs');
const path = require('path');

const assetsDir = 'facial_parts_new';
const featureAssets = {};

console.log('Scanning for image assets...');

// Get all the category folders (e.g., 'head', 'hairs')
const categories = fs.readdirSync(assetsDir).filter(file => {
    return fs.statSync(path.join(assetsDir, file)).isDirectory();
});

// Loop through each category folder
for (const category of categories) {
    const categoryPath = path.join(assetsDir, category);
    const files = fs.readdirSync(categoryPath);

    // Get the full relative paths of all image files in the folder
    const imagePaths = files
        .filter(file => /\.(png|jpg|jpeg|gif|svg)$/i.test(file)) // Only include image files
        .map(file => `${assetsDir}/${category}/${file}`); // Create the full path, e.g., "facial parts-new/head/oval.png"

    if (imagePaths.length > 0) {
        featureAssets[category] = imagePaths;
    }
}

// Format the final object as a string and print it to the console
const output = `const featureAssets = ${JSON.stringify(featureAssets, null, 4)};`;

console.log('\n Success! Copy the code below and paste it into your index.html file:\n');
console.log(output);

