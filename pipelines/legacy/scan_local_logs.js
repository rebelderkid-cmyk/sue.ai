const fs = require('fs');
const path = require('path');

// Point to the correct subdirectory
const LOG_DIR = path.join(__dirname, 'logs_analyzed/logs');

console.log(`📋 Analyzing Logs from: ${LOG_DIR}`);
console.log(`-----------------------------------------------------------------------`);

if (!fs.existsSync(LOG_DIR)) {
    console.log(`❌ Error: Directory not found. Did you download logs?`);
    process.exit(1);
}

const files = fs.readdirSync(LOG_DIR).filter(f => f.startsWith('status_worker_'));
const workers = [];

files.forEach(f => {
    try {
        const data = JSON.parse(fs.readFileSync(path.join(LOG_DIR, f)));
        workers.push(data);
    } catch (e) {
        console.log(`⚠️  Corrupt file ${f}`);
    }
});

workers.sort((a, b) => parseInt(a.workerId) - parseInt(b.workerId));

console.log(`| ID | Range        | Status                  | Page      | Found | Success | Error |`);
console.log(`|----|--------------|-------------------------|-----------|-------|---------|-------|`);

workers.forEach(w => {
    const id = w.workerId.toString().padEnd(2);
    const range = `${w.config.start}-${w.config.end}`.padEnd(12);
    const status = (w.status || 'Unknown').substring(0, 23).padEnd(23);
    const page = `${w.currentPage}/${w.totalPages || '?'}`.padEnd(9);
    const found = (w.totalPages > 0) ? 'Yes' : 'No ';
    const success = (w.successCount || 0).toString().padEnd(7);
    const error = (w.errorCount || 0).toString().padEnd(5);

    console.log(`| ${id} | ${range} | ${status} | ${page} | ${found}   | ${success} | ${error} |`);
});

console.log(`-----------------------------------------------------------------------`);
