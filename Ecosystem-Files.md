PM2 is a really good fit for this architecture because you’ve got multiple long-running realtime services:

Horus
Sensei
ZMQ/WebSocket bridge
Vite frontend
Eventually:
Redis
recording service
analytics workers
clip generator
mobile sync service

We can manage all of it from one ecosystem file.

Install PM2
```bash
npm install -g pm2
```


Start Everything

From the root:

```
pm2 start ecosystem.dev.config.cjs
```

## Useful PM2 Commands

View running services
```
pm2 ls
```

Live logs
```
pm2 logs
```
Single service:
```
pm2 logs sensei
```
Restart one service
```
pm2 restart sensei
```
Restart all
```
pm2 restart all
```
Stop all
```
pm2 stop all
```
Auto-start on reboot

Generate startup script:
```
pm2 startup
```
Then save current processes:
```
pm2 save
```
Now the squat-analysis stack survives reboots automatically.

Recommended Upgrade: Production Frontend

Eventually don’t run Vite dev server in production.

Instead:
```
npm run build
```
Then serve with:
```
npm install -g serve
```
PM2 config:
```
{
  name: "frontend",
  script: "serve",
  args: "-s dist -l 4173",
  cwd: "./frontend",
}
```
That gives you:

much lower CPU
faster startup
cleaner logs
proper static serving
Bonus: Single Dev Bootstrap Script
dev.sh
```
#!/bin/bash

pm2 start ecosystem.config.cjs

pm2 logs
```

Make executable:
```
chmod +x dev.sh
```
Run:

./dev.sh
Bonus: Health Monitoring

PM2 gives ue:
```
pm2 monit
```

see:

CPU usage
memory
restarts
crashes
logs
process uptime

Super useful for realtime CV systems.