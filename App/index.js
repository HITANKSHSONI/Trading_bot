const express = require("express");
const http = require("http");
const { spawn } = require("child_process");
const cors = require("cors");
const socketIo = require("socket.io");
const path = require("path");

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

app.use(cors());
app.use(express.json());

// Serve frontend files
app.use(express.static(path.join(__dirname, "public")));

// Route to trigger Python script
app.post("/start-trading", (req, res) => {
    const pythonProcess = spawn("python3", ["Live_trading_with_Supertrend_finalll.py"]);

    pythonProcess.stdout.on("data", (data) => {
        console.log(`Python Output: ${data}`);
        io.emit("log", data.toString()); // Send log data to frontend
    });

    pythonProcess.stderr.on("data", (data) => {
        console.error(`Python Error: ${data}`);
        io.emit("log", `Error: ${data.toString()}`);
    });

    pythonProcess.on("close", (code) => {
        console.log(`Python process exited with code ${code}`);
        io.emit("log", `Process exited with code ${code}`);
    });

    res.json({ message: "Trading started. Check logs on the dashboard." });
});

// Start the server
const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

