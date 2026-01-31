const fs = require('fs');
const { PDFParse } = require('pdf-parse');

// Pick one of the existing files
const pdfPath = 'downloads/2568/Deka_6267-2568_(Ref720024).pdf';

if (!fs.existsSync(pdfPath)) {
    console.error('Test file not found!');
    process.exit(1);
}

const dataBuffer = fs.readFileSync(pdfPath);

console.log(`📄 Extracting text from: ${pdfPath}`);
console.log('-----------------------------------');

PDFParse(dataBuffer).then(function (data) {
    // PDF text
    console.log(data.text);
    console.log('-----------------------------------');
    console.log(`Length: ${data.text.length} characters`);
}).catch(err => {
    console.error('Extraction Error:', err);
});
