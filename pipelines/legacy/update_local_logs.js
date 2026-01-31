const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(__dirname, 'logs_analyzed/logs');

// 10-WORKER CONFIG (Full Ranges)
const RANGES = [
    { id: '1', start: '2462', end: '2473', total: 347 },
    { id: '2', start: '2474', end: '2485', total: 393 },
    { id: '3', start: '2486', end: '2497', total: 500 },
    { id: '4', start: '2498', end: '2509', total: 508 },
    { id: '5', start: '2510', end: '2519', total: 530 },
    { id: '6', start: '2520', end: '2529', total: 825 },
    { id: '7', start: '2530', end: '2539', total: 1744 },
    { id: '8', start: '2540', end: '2549', total: 984 },
    { id: '9', start: '2550', end: '2559', total: 559 },
    { id: '10', start: '2560', end: '2569', total: 261 }
];

if (!fs.existsSync(LOG_DIR)) {
    console.log(`❌ Directory not found: ${LOG_DIR}`);
    process.exit(1);
}

RANGES.forEach(range => {
    const filePath = path.join(LOG_DIR, `status_worker_${range.id}.json`);

    const data = {
        workerId: range.id,
        lastUpdated: new Date().toISOString(),
        config: {
            start: range.start,
            end: range.end
        },
        currentPage: 1,  // Start fresh from page 1
        totalPages: range.total,
        successCount: 0,
        errorCount: 0,
        status: "Ready to Resume"
    };

    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    console.log(`Worker ${range.id}: Reset to Page 1 / Total ${range.total}`);
});

console.log(`✅ All 10 worker logs generated. Cache will skip existing files.`);
