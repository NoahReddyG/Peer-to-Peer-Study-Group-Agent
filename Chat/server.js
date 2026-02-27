const express = require("express")
const http = require("http")
const { Server } = require("socket.io")
const fs = require("fs")

const app = express()
const server = http.createServer(app)

const io = new Server(server, {
  cors: { origin: "*" }
})

const users = {}
const MESSAGE_FILE = "messages.json"

const loadMessages = () => {
  if (!fs.existsSync(MESSAGE_FILE)) return []
  const data = fs.readFileSync(MESSAGE_FILE)
  return JSON.parse(data)
}

const saveMessage = (message) => {
  const messages = loadMessages()
  messages.push(message)
  fs.writeFileSync(MESSAGE_FILE, JSON.stringify(messages, null, 2))
}

io.on("connection", (socket) => {
  const history = loadMessages()
  socket.emit("history", history)

  socket.on("register", (username) => {
    if (!username || typeof username !== "string") return
    users[socket.id] = username
  })

  socket.on("message", (text) => {
    if (!text || typeof text !== "string") return
    const sender = users[socket.id]
    if (!sender) return

    const message = {
      sender,
      text,
      timestamp: Date.now()
    }

    saveMessage(message)
    io.emit("message", message)
  })

  socket.on("disconnect", () => {
    delete users[socket.id]
  })
})

server.listen(3000)