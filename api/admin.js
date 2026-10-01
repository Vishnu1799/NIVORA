let globalBankState = {
  state: 'UP',
  failure_rate: 0.0,
  force_outcome: null,
  response_delay_ms: 0,
  transaction_count: 0,
  state_changed_at: new Date().toISOString(),
  signals: {},
  latest_signal: null,
};

module.exports = (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', '*');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const path = req.url || '';

  if (req.method === 'POST') {
    let body = req.body || {};
    if (typeof body === 'string') {
      try { body = JSON.parse(body); } catch(e) {}
    }

    if (path.includes('signal')) {
      const signal = (body.signal || '').toUpperCase();
      globalBankState.latest_signal = signal;
      if (body.transaction_id) {
        globalBankState.signals[body.transaction_id] = signal;
      }
      if (signal === 'INSTANT_SUCCESS') {
        globalBankState.force_outcome = 'SUCCESS';
        globalBankState.state = 'UP';
      } else {
        globalBankState.force_outcome = signal;
        globalBankState.state = signal;
      }
      globalBankState.state_changed_at = new Date().toISOString();
      return res.status(200).json({ success: true, signal, state: globalBankState.state });
    }

    if (path.includes('reset')) {
      globalBankState.state = 'UP';
      globalBankState.force_outcome = null;
      globalBankState.failure_rate = 0.0;
      globalBankState.signals = {};
      globalBankState.latest_signal = null;
      globalBankState.state_changed_at = new Date().toISOString();
      return res.status(200).json({ success: true, message: 'Reset to UP' });
    }

    // Service state update
    if (body.state) globalBankState.state = body.state.toUpperCase();
    if (body.force_outcome !== undefined) globalBankState.force_outcome = body.force_outcome ? body.force_outcome.toUpperCase() : null;
    if (body.failure_rate !== undefined) globalBankState.failure_rate = body.failure_rate;
    globalBankState.state_changed_at = new Date().toISOString();

    return res.status(200).json({
      success: true,
      state: globalBankState.state,
      force_outcome: globalBankState.force_outcome,
      changed_at: globalBankState.state_changed_at,
    });
  }

  // GET State
  return res.status(200).json({
    state: globalBankState.state,
    force_outcome: globalBankState.force_outcome,
    failure_rate: globalBankState.failure_rate,
    response_delay_ms: globalBankState.response_delay_ms,
    transaction_count: globalBankState.transaction_count,
    state_changed_at: globalBankState.state_changed_at,
    latest_signal: globalBankState.latest_signal,
  });
};
