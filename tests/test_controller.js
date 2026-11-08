const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const flows = JSON.parse(fs.readFileSync(path.join(__dirname, '../nodered/flows.json')));
const fn = flows.find(n => n.id === 'recommend').func;
let now = 1000000;
const values = {};
let requested = 'AUTO';
const context = {get: k => values[k], set: (k, v) => { values[k] = v; }};
const flow = {get: () => requested};
const node = {status: () => {}};
function run(topic, payload, retain = false) {
  const sandbox = {msg: {topic, payload, retain}, context, flow, node, Date: {now: () => now}};
  return vm.runInNewContext(`(function(){${fn}})()`, sandbox).payload;
}
assert.equal(run('tick', 0), 'FAILSAFE');
run('hvac/roof/temp_out', 30);
run('hvac/house/temp_return', 20);
run('hvac/mass/temp_out', 23);
assert.equal(run('hvac/core/temp', 20, true), 'FAILSAFE');
assert.equal(run('hvac/core/temp', 20), 'CHARGE_THERMAL_MASS');
assert.equal(run('hvac/roof/temp_out', 21), 'HEAT_HOUSE');
assert.equal(run('hvac/mass/temp_out', 20), 'IDLE');
assert.equal(run('hvac/roof/temp_out', 15), 'NIGHT_COOLING');
requested = 'DIAGNOSTICS';
assert.equal(run('tick', 0), 'DIAGNOSTICS');
requested = 'IDLE';
assert.equal(run('tick', 0), 'IDLE');
assert.equal(run('hvac/core/temp', 'bad'), 'FAILSAFE');
run('hvac/core/temp', 20);
assert.equal(run('hvac/core/temp', null), 'FAILSAFE');
run('hvac/core/temp', 20);
now += 120000;
assert.equal(run('tick', 0), 'FAILSAFE');
const writer = flows.find(n => n.id === 'line').func;
function write(topic, payload, retain = false) {
  const env = {get: k => ({INFLUX_URL: 'http://influxdb:8086', INFLUX_ORG: 'hvac',
    INFLUX_BUCKET: 'hvac', INFLUX_TOKEN: 'test'}[k])};
  return vm.runInNewContext(`(function(){${writer}})()`,
    {msg: {topic, payload, retain}, env, node, Date: {now: () => now}});
}
assert.equal(write('hvac/core/temp', null), null);
assert.equal(write('hvac/core/temp', true), null);
assert.equal(write('hvac/core/temp', 20, true), null);
assert.equal(write('hvac/unknown', 20), null);
assert.equal(write('hvac/core/temp', '20.5').payload, `hvac core=20.5 ${now}`);
console.log('Controller advisory transitions passed');
