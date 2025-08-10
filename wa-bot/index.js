// wa-bot/index.js
import http from "http";
import path from "path";
import fs from "fs/promises";
import { fileURLToPath } from "url";
import express from "express";
import cors from "cors";
import SSE from "express-sse";
import pkg from "whatsapp-web.js";

const { Client, LocalAuth, MessageMedia } = pkg;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SESSION_ROOT = path.resolve(__dirname, ".wwebjs_auth");
const CLIENT_ID = "bot01";

const app = express();
app.use(cors());
app.use(express.json());

// SSE para QR/estado
const sse = new SSE();
app.get("/wa/events", (req, res) => sse.init(req, res));

// página estática do dashboard
app.use(express.static(path.join(__dirname, "public"))); // deve conter wa_dashboard.html

// helpers
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function safeRmDir(dir, attempts = 10, delayMs = 400) {
  for (let i = 0; i < attempts; i++) {
    try {
      await fs.rm(dir, { recursive: true, force: true });
      return true;
    } catch (err) {
      // EBUSY/EPERM no Windows: tenta de novo
      if (i === attempts - 1) throw err;
      await sleep(delayMs);
    }
  }
}

function sessionDir() {
  return path.join(SESSION_ROOT, `session-${CLIENT_ID}`);
}

let client = null;
let initializing = false;

async function createClient() {
  if (initializing) return;
  initializing = true;

  client = new Client({
    authStrategy: new LocalAuth({
      clientId: CLIENT_ID,
      dataPath: SESSION_ROOT,
      // 🔑 ESSENCIAL: não apagar automaticamente (evita EBUSY)
      deleteSessionDataOnLogout: false,
    }),
    puppeteer: {
      headless: true,
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--log-level=3",
        "--disable-logging",
      ],
      // Opcional: redireciona log do Chromium (evita chrome_debug.log)
      env: { CHROME_LOG_FILE: process.platform === "win32" ? "NUL" : "/dev/null" },
    },
    // reconexão automática é feita por nós
    takeoverOnConflict: true,
    takeoverTimeoutMs: 0,
  });

  // Eventos
  client.on("qr", (qr) => {
    sse.send({ type: "qr", qr });
  });

  client.on("ready", () => {
    console.log("🤖 Pronto (ready)");
    sse.send({ type: "ready" });
  });

  client.on("authenticated", () => {
    console.log("🔐 Autenticado");
    sse.send({ type: "authenticated" });
  });

  client.on("auth_failure", (m) => {
    console.warn("⚠️ Falha de autenticação:", m);
    sse.send({ type: "auth_failure", message: m });
  });

  client.on("disconnected", async (reason) => {
    console.warn("⚠️ Desconectado:", reason);
    sse.send({ type: "disconnected", reason });

    try {
      // fecha o browser e solta os handles de arquivo
      await client.destroy();
    } catch (e) {
      console.warn("destroy() falhou (ok continuar):", e?.message);
    }

    // Se foi LOGOUT, limpar sessão (com retry para contornar EBUSY)
    if (String(reason).toUpperCase() === "LOGOUT") {
      const dir = sessionDir();
      try {
        await sleep(1200); // dá tempo do Chromium soltar locks
        await safeRmDir(dir); // remove pasta da sessão com tentativas
        console.log("🧹 sessão limpa:", dir);
      } catch (e) {
        console.error("Erro ao limpar sessão:", e?.message);
      }
    }

    // Recria o cliente para exibir QR novamente (ou reconectar)
    initializing = false;
    await sleep(1000);
    await createClient();
  });

  // Só responde chats privados; ignora grupos, status e verificados (broadcast)
  client.on("message", async (msg) => {
    try {
      // Ignora status/broadcast/MD
      if (msg.from === "status@broadcast") return;
      // Verifica se é grupo
      const chat = await msg.getChat();
      if (chat.isGroup) return;

      // Se chegou aqui, é 1:1 – retransmitimos ao frontend
      sse.send({
        type: "message",
        from: msg.from,
        body: msg.body,
        timestamp: msg.timestamp,
      });

      // Chame seu backend FastAPI para obter resposta RAG (ou use local)
      // Exemplo simples: encaminha para seu endpoint /api/chat/message
      const answer = await fetch("http://127.0.0.1:8000/api/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg.body, session_id: msg.from }),
      })
        .then((r) => r.json())
        .then((d) => d?.resposta || "Não consegui responder agora.");

      // responde no WhatsApp
      await client.sendMessage(msg.from, answer);
      // notifica o dashboard web também
      sse.send({ type: "bot_message", to: msg.from, body: answer });
    } catch (e) {
      console.error("Erro ao processar mensagem:", e?.message);
    }
  });

  try {
    await client.initialize();
  } catch (e) {
    console.error("Falha ao inicializar cliente:", e?.message);
    initializing = false;
    await sleep(1500);
    return createClient();
  }

  initializing = false;
}

// endpoints utilitários do bot
app.post("/wa/restart", async (_req, res) => {
  try {
    if (client) await client.destroy();
  } catch {}
  await createClient();
  res.json({ ok: true });
});

app.post("/wa/logout", async (_req, res) => {
  try {
    if (client) await client.destroy();
  } catch {}
  try {
    await safeRmDir(sessionDir());
  } catch (e) {
    return res.status(500).json({ ok: false, error: e?.message });
  }
  await createClient();
  res.json({ ok: true });
});

const server = http.createServer(app);
const PORT = process.env.WA_PORT || 3001;
server.listen(PORT, () => {
  console.log(`WA socket server on http://127.0.0.1:${PORT}`);
  createClient();
});
