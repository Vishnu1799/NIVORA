const transactions = {};
let txnCount = 0;

module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', '*');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const url = req.url || '';

  // 1. Get Payment Status: /api/payments/:id/status
  if (req.method === 'GET') {
    const parts = url.split('/');
    const txnId = parts.find(p => p.startsWith('TXN_')) || parts[2];

    let txn = transactions[txnId];
    if (!txn) {
      txn = {
        transaction_id: txnId || `TXN_${Date.now()}`,
        status: 'SUCCESS',
        amount: 249.0,
        failure_code: null,
        money_debited: true,
      };
    }

    // Check if under verification expired (7 seconds)
    if (txn.status === 'UNDER_VERIFICATION') {
      const elapsed = (Date.now() - (txn.created_ts || Date.now())) / 1000;
      if (elapsed > 7) {
        // Expired without success signal -> SAFE_RETURN
        txn.status = 'SAFE_RETURN';
        txn.failure_code = 'TIMEOUT_RESOLVED';
        txn.failure_reason = 'Payment could not be confirmed. ₹0 was debited. Safe to retry.';
        txn.money_debited = false;
      }
    }

    return res.status(200).json(txn);
  }

  // 2. Create Payment: POST /api/payments
  if (req.method === 'POST') {
    let body = req.body || {};
    if (typeof body === 'string') {
      try { body = JSON.parse(body); } catch(e) {}
    }

    txnCount++;
    const txnId = `TXN_${Date.now().toString(16).toUpperCase()}`;
    const amount = body.amount || 249.0;
    const orderId = body.order_id || `ORD_${Date.now()}`;

    // Get current bank state from admin module
    let adminModule;
    try {
      adminModule = require('./admin.js');
    } catch(e) {}

    // Check bank condition
    let bankState = 'UP';
    let forceOutcome = null;

    // Check query / environment / headers
    if (global.globalBankState) {
      bankState = global.globalBankState.state || 'UP';
      forceOutcome = global.globalBankState.force_outcome;
    }

    const activeState = (forceOutcome || bankState).toUpperCase();

    let responseData = {};

    if (activeState === 'INSUFFICIENT_FUNDS' || activeState === 'FAILED') {
      responseData = {
        transaction_id: txnId,
        order_id: orderId,
        status: 'DECLINED',
        amount: amount,
        currency: 'INR',
        failure_code: 'INSUFFICIENT_FUNDS',
        failure_reason: 'Decline Code 51: Insufficient funds in customer account',
        message: 'Payment declined: Insufficient funds in customer account',
        money_debited: false,
        created_ts: Date.now(),
      };
    } else if (activeState === 'DOWN') {
      responseData = {
        transaction_id: txnId,
        order_id: orderId,
        status: 'DECLINED',
        amount: amount,
        currency: 'INR',
        failure_code: 'BANK_UNAVAILABLE',
        failure_reason: '503 Service Unavailable: Core banking system offline',
        message: 'Payment declined: Bank unavailable',
        money_debited: false,
        created_ts: Date.now(),
      };
    } else if (activeState === 'INVALID_DETAILS' || activeState === 'INVALID_PIN') {
      responseData = {
        transaction_id: txnId,
        order_id: orderId,
        status: 'DECLINED',
        amount: amount,
        currency: 'INR',
        failure_code: 'INVALID_DETAILS',
        failure_reason: 'Decline Code 55: Incorrect UPI PIN or card credentials',
        message: 'Payment declined: Incorrect credentials',
        money_debited: false,
        created_ts: Date.now(),
      };
    } else if (activeState === 'ERROR_SIGNAL' || activeState === 'TIMEOUT' || activeState === 'NO_RESPONSE') {
      responseData = {
        transaction_id: txnId,
        order_id: orderId,
        status: 'UNDER_VERIFICATION',
        amount: amount,
        currency: 'INR',
        failure_code: 'TIMEOUT_UNCERTAIN',
        failure_reason: 'Gateway response uncertain. Verification in progress.',
        message: 'Payment is under verification by AUREV AI.',
        money_debited: null,
        created_ts: Date.now(),
      };
    } else {
      responseData = {
        transaction_id: txnId,
        order_id: orderId,
        status: 'SUCCESS',
        amount: amount,
        currency: 'INR',
        message: 'Payment completed successfully',
        money_debited: true,
        created_ts: Date.now(),
      };
    }

    transactions[txnId] = responseData;
    return res.status(200).json(responseData);
  }

  return res.status(405).json({ error: 'Method Not Allowed' });
};
