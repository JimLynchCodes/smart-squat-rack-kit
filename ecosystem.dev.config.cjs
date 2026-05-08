module.exports = {
  apps: [
    {
      name: "horus",

      script: "main.py",

      cwd: "./horus",

      interpreter: "python3",

      watch: false,

      autorestart: true,

      env: {
        PYTHONUNBUFFERED: "1",
      },
    },

    {
      name: "sensei",

      script: "main.py",

      cwd: "./sensei",

      interpreter: "python3",

      watch: false,

      autorestart: true,

      env: {
        PYTHONUNBUFFERED: "1",
      },
    },

    {
      name: "bridge",

      script: "server.js",

      cwd: "./bridge",

      interpreter: "node",

      watch: false,

      autorestart: true,
    },

    {
      name: "frontend",

      script: "npm",

      args: "run dev -- --host 0.0.0.0",

      cwd: "./frontend",

      interpreter: "none",

      watch: false,

      autorestart: true,
    },
  ],
};