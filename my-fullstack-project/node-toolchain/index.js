const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

// Middleware to parse JSON bodies
app.use(express.json());

// Example route
app.get('/', (req, res) => {
    res.send('Welcome to the Node Toolchain!');
});

// Start the server
app.listen(port, () => {
    console.log(`Node Toolchain running at http://localhost:${port}`);
});