/**
 * vAPI x402 Multi-Wallet Quote API — Cloudflare Worker
 * 
 * Fitur:
 * - Mendukung 10 wallet sekaligus dalam 1 Worker gratis!
 * - /quote              -> Menggunakan Default Wallet 1
 * - /quote/0x<address>  -> Menggunakan Wallet sesuai alamat di URL
 * - /quote?wallet=0x... -> Alternatif query parameter
 * 
 * Network: Base Mainnet (eip155:8453)
 * Asset: USDC Base (0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)
 * Facilitator: https://facilitator.payai.network
 */

// Default fallback address (gunakan /quote/{walletAddress} atau set variabel PAY_TO di Cloudflare)
const DEFAULT_PAY_TO = "0x0000000000000000000000000000000000000000";
const FACILITATOR = "https://facilitator.payai.network";
const NETWORK = "eip155:8453";
const ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913";
const AMOUNT = "1000";

const QUOTES = [
  "The secret of getting ahead is getting started. - Mark Twain",
  "It always seems impossible until it's done. - Nelson Mandela",
  "Well done is better than well said. - Benjamin Franklin",
  "Simplicity is the ultimate sophistication. - Leonardo da Vinci",
  "Act as if what you do makes a difference. It does. - William James",
  "The best way to predict the future is to create it. - Peter Drucker",
  "Innovation distinguishes between a leader and a follower. - Steve Jobs",
  "Do what you can, with what you have, where you are. - Theodore Roosevelt"
];

function getPayTo(url) {
  // Check path parameter: /quote/0x...
  const pathMatch = url.pathname.match(/\/quote\/(0x[a-fA-F0-9]{40})/i);
  if (pathMatch) return pathMatch[1];

  // Check query parameter: ?wallet=0x... or ?payTo=0x...
  const queryWallet = url.searchParams.get("wallet") || url.searchParams.get("payTo");
  if (queryWallet && /^0x[a-fA-F0-9]{40}$/i.test(queryWallet)) {
    return queryWallet;
  }

  return DEFAULT_PAY_TO;
}

function requirements(url, payTo) {
  return {
    scheme: "exact",
    network: NETWORK,
    amount: AMOUNT,
    maxAmountRequired: AMOUNT,
    asset: ASSET,
    payTo: payTo,
    resource: url,
    description: "One random inspirational quote",
    mimeType: "application/json",
    maxTimeoutSeconds: 120,
    extra: { name: "USD Coin", version: "2" },
  };
}

const json = (obj, status = 200, headers = {}) =>
  new Response(JSON.stringify(obj), {
    status,
    headers: {
      "content-type": "application/json",
      "access-control-allow-origin": "*",
      "access-control-expose-headers": "PAYMENT-REQUIRED, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE",
      ...headers,
    },
  });

const b64 = (o) => btoa(JSON.stringify(o));
const unb64 = (s) => JSON.parse(atob(s));

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const base = url.origin;
    const payTo = getPayTo(url);
    const req = requirements(url.href, payTo);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "access-control-allow-origin": "*",
          "access-control-allow-headers": "*",
          "access-control-allow-methods": "GET, OPTIONS",
        },
      });
    }

    if (url.pathname === "/") {
      return json({ 
        name: "vAPI Multi-Wallet Quote API", 
        paid: "/quote",
        endpoints: ["/quote", "/quote/{wallet}"] 
      });
    }

    if (url.pathname === "/openapi.json") {
      return json({
        openapi: "3.0.3",
        info: { 
          title: "vAPI Quote API", 
          version: "1.0.0", 
          description: "Random quote API powered by x402 on Base mainnet" 
        },
        servers: [{ url: base }],
        paths: {
          "/quote": {
            get: {
              summary: "Get a random quote",
              "x-payment-info": {
                scheme: "exact", 
                network: NETWORK, 
                amount: AMOUNT,
                asset: ASSET, 
                payTo: DEFAULT_PAY_TO, 
                maxTimeoutSeconds: 120,
                extra: { name: "USD Coin", version: "2" },
              },
              responses: {
                "200": { description: "Quote" },
                "402": { description: "Payment required" },
              },
            },
          },
          "/quote/{wallet}": {
            get: {
              summary: "Get a random quote with custom payout wallet",
              parameters: [
                {
                  name: "wallet",
                  in: "path",
                  required: true,
                  schema: { type: "string" }
                }
              ],
              "x-payment-info": {
                scheme: "exact", 
                network: NETWORK, 
                amount: AMOUNT,
                asset: ASSET, 
                payTo: payTo, 
                maxTimeoutSeconds: 120,
                extra: { name: "USD Coin", version: "2" },
              },
              responses: {
                "200": { description: "Quote" },
                "402": { description: "Payment required" },
              },
            },
          },
        },
      });
    }

    if (url.pathname === "/.well-known/x402") {
      return json({
        x402Version: 2,
        resources: [base + "/quote", url.href],
        accepts: [req]
      });
    }

    if (url.pathname === "/quote" || url.pathname.startsWith("/quote/")) {
      const header =
        request.headers.get("PAYMENT-SIGNATURE") ||
        request.headers.get("X-PAYMENT");

      const challenge = {
        x402Version: 2,
        error: "Payment required",
        resource: {
          url: req.resource,
          description: req.description,
          mimeType: req.mimeType,
        },
        accepts: [req],
      };

      if (!header) {
        return json(challenge, 402, { "PAYMENT-REQUIRED": b64(challenge) });
      }

      let paymentPayload;
      try {
        paymentPayload = unb64(header);
      } catch {
        return json({ ...challenge, error: "Bad payment header" }, 402, {
          "PAYMENT-REQUIRED": b64(challenge),
        });
      }

      const body = JSON.stringify({
        x402Version: paymentPayload.x402Version || 2,
        paymentPayload,
        paymentRequirements: req,
      });
      const opts = {
        method: "POST",
        headers: { "content-type": "application/json" },
        body,
      };

      const v = await (await fetch(FACILITATOR + "/verify", opts))
        .json().catch(() => ({}));
      if (!v.isValid) {
        return json(
          { ...challenge, error: v.invalidReason || "Payment invalid" },
          402,
          { "PAYMENT-REQUIRED": b64(challenge) }
        );
      }

      const s = await (await fetch(FACILITATOR + "/settle", opts))
        .json().catch(() => ({}));
      if (!s.success) {
        return json(
          { ...challenge, error: s.errorReason || "Settlement failed" },
          402,
          { "PAYMENT-REQUIRED": b64(challenge) }
        );
      }

      const quote = QUOTES[Math.floor(Math.random() * QUOTES.length)];
      return json({ quote }, 200, {
        "PAYMENT-RESPONSE": b64(s),
        "X-PAYMENT-RESPONSE": b64(s),
      });
    }

    return json({ error: "Not found" }, 404);
  },
};
