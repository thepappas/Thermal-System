const fs = require("fs");
const secret = (name) => fs.readFileSync(`/run/hvac-secrets/${name}`, "utf8").trim();

module.exports = {
    flowFile: "flows.json",
    credentialSecret: secret("nodered-credential-secret"),
    adminAuth: {
        type: "credentials",
        users: [{
            username: process.env.NODE_RED_ADMIN_USER,
            password: secret("nodered-admin-hash"),
            permissions: "*"
        }]
    },
    functionExternalModules: false
};
