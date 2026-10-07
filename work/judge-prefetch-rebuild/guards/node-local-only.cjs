// Execution-only fixture guard, inherited by the actual Pi SDK Node worker.
const net = require('node:net');
const fs = require('node:fs');
const path = require('node:path');
function local(host) {
  return host === undefined || host === 'localhost' || host === '::1' || /^127\./.test(host);
}
const originalConnect = net.Socket.prototype.connect;
net.Socket.prototype.connect = function (...args) {
  const options = Array.isArray(args[0]) ? args[0][0] : args[0];
  const host = typeof options === 'object' ? options.host : typeof args[1] === 'string' ? args[1] : undefined;
  if (!local(host)) throw new Error('Controlled verification forbids non-loopback Node sockets');
  return originalConnect.apply(this, args);
};
for (const method of ['readFileSync', 'readFile']) {
  const original = fs[method];
  fs[method] = function (file, ...args) {
    if (typeof file === 'string' || file instanceof URL) {
      const name = path.basename(String(file));
      if (name === '.env' || name.startsWith('.env.')) throw new Error('Controlled verification forbids dotenv reads');
    }
    return original.call(this, file, ...args);
  };
}
