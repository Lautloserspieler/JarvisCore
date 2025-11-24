window.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('authenticator-modal');
  const secretEl = document.getElementById('authenticator-secret');
  const uriEl = document.getElementById('authenticator-uri');
  const qrEl = document.getElementById('authenticator-qr');
  const confirmBtn = document.getElementById('authenticator-confirm');
  const loadingEl = document.getElementById('authenticator-loading');
  const codeInput = document.getElementById('authenticator-code');
  const errorEl = document.getElementById('authenticator-error');
  const successEl = document.getElementById('authenticator-success');
  const copyBtn = document.getElementById('authenticator-copy');
  const closeBtn = document.getElementById('authenticator-close');
  const cancelBtn = document.getElementById('authenticator-cancel');
  const modalBg = modal ? modal.querySelector('.modal-background') : null;
  const statusEl = document.getElementById('authenticator-status');
  const openBtn = document.getElementById('authenticator-open');
  const isFileProtocol = window.location.protocol === 'file:';
  let pendingSetup = null;

  async function fetchSecurityStatus() {
    if (isFileProtocol) {
      updateStatus('Offline-Ansicht: Bitte starte JarvisCore und öffne diese Seite über http://127.0.0.1:5050/static/security.html.', 'warning');
      return;
    }
    if (statusEl && statusEl.dataset.state !== 'warning' && statusEl.dataset.state !== 'success') {
      updateStatus('Prüfe Sicherheitsstatus …', 'info');
    }
    try {
      const response = await fetch('/api/security/status', { headers: defaultHeaders() });
      if (response.status === 401 || response.status === 403) {
        showTokenWarning();
        return;
      }
      if (!response.ok) {
        throw new Error(`Status ${response.status}`);
      }
      const payload = await response.json();
      if (payload && payload.security) {
        handleSecurityPayload(payload.security);
      }
    } catch (err) {
      console.error('Sicherheitsstatus konnte nicht geladen werden', err);
      if (!statusEl || statusEl.dataset.state !== 'warning') {
        updateStatus('Sicherheitsstatus konnte nicht geladen werden.', 'danger');
      }
    }
  }

  function handleSecurityPayload(security) {
    const authenticator = security.authenticator || {};
    const needsSetup = !!authenticator.needs_setup;
    const pending = authenticator.pending_setup || null;
    pendingSetup = pending;
    if (needsSetup && pending) {
      console.debug('Authenticator pending payload', pending);
      showAuthenticatorSetup(pending);
      updateStatus('Es ist noch keine Authenticator-App hinterlegt. Bitte schließe die Einrichtung ab.', 'warning');
    } else if (needsSetup) {
      updateStatus('Authenticator-Einrichtung wird vorbereitet …', 'info');
      hideAuthenticatorSetup();
    } else {
      updateStatus('Die Zwei-Faktor-Authentifizierung ist aktiv.', 'success');
      hideAuthenticatorSetup();
    }
  }

  function showAuthenticatorSetup(pending) {
    if (!modal) {
      console.warn('Authenticator-Modal nicht vorhanden.');
      return;
    }
    resetAuthenticatorForm();
    const secret = pending.secret || '---';
    secretEl.textContent = secret;
    uriEl.textContent = pending.provisioning_uri || '';
    uriEl.href = pending.provisioning_uri || '#';
    if (qrEl) {
      qrEl.innerHTML = '';
      const info = document.getElementById('authenticator-info');
      if (info) {
        info.classList.add('is-hidden');
      }
      if (window.QRCode && pending.provisioning_uri) {
        new window.QRCode(qrEl, {
          text: pending.provisioning_uri,
          width: 196,
          height: 196,
          correctLevel: window.QRCode.CorrectLevel && window.QRCode.CorrectLevel.H ? window.QRCode.CorrectLevel.H : undefined,
        });
        if (info) {
          info.classList.remove('is-hidden');
        }
      } else {
        if (pending.provisioning_uri) {
          const img = document.createElement('img');
          const googleUrl = `https://chart.googleapis.com/chart?cht=qr&chs=196x196&chl=${encodeURIComponent(
            pending.provisioning_uri,
          )}`;
          const localUrl = !isFileProtocol
            ? `/api/security/authenticator/qr?ts=${Date.now().toString()}`
            : null;
          let triedGoogle = !localUrl;
          img.alt = 'Authenticator QR Code';
          img.loading = 'lazy';
          img.referrerPolicy = triedGoogle ? 'no-referrer' : 'strict-origin-when-cross-origin';
          img.onerror = () => {
            if (!triedGoogle) {
              triedGoogle = true;
              img.referrerPolicy = 'no-referrer';
              img.src = googleUrl;
              return;
            }
            img.remove();
            appendFallbackMessage(qrEl, pending.provisioning_uri, secret);
            if (info) {
              info.classList.remove('is-hidden');
            }
          };
          img.src = localUrl || googleUrl;
          qrEl.appendChild(img);
          if (info) {
            info.classList.remove('is-hidden');
          }
        } else {
          appendFallbackMessage(qrEl, null, secret);
          if (info) {
            info.classList.remove('is-hidden');
          }
        }
      }
    }
    modal.classList.add('is-active');
    updateStatus('Es ist noch keine Authenticator-App hinterlegt. Bitte schließe die Einrichtung ab.', 'warning');
  }

  function hideAuthenticatorSetup() {
    if (modal) {
      modal.classList.remove('is-active');
      resetAuthenticatorForm();
    }
  }

  function showTokenWarning() {
    const note = document.getElementById('authenticator-token-warning');
    if (note) {
      note.classList.remove('is-hidden');
    }
    updateStatus('Bitte gib zuerst den Web-Token ein, bevor du den Authenticator verknüpfst.', 'warning');
  }

  async function confirmSetup() {
    if (!pendingSetup) {
      return;
    }
    const code = (codeInput ? codeInput.value : '').trim();
    if (code.length !== 6) {
      showError('Bitte gib einen 6-stelligen Code ein.');
      return;
    }
    if (isFileProtocol) {
      showError('Code-Bestätigung ist im Offline-Modus nicht möglich. Öffne die Weboberfläche über http://127.0.0.1:5050/static/security.html.');
      updateStatus('Zur Bestätigung bitte die Weboberfläche über den lokalen Server öffnen.', 'warning');
      return;
    }
    hideElement(errorEl);
    hideElement(successEl);
    try {
      showElement(loadingEl);
      if (confirmBtn) {
        confirmBtn.disabled = true;
      }
      const response = await fetch('/api/security/authenticator/confirm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...defaultHeaders(),
        },
        body: JSON.stringify({ code: code.trim() }),
      });
      const payload = await response.json();
      if (!response.ok || payload.status !== 'ok') {
        showError(payload.message || 'Der Code wurde nicht akzeptiert.');
        return;
      }
      showSuccess('Authenticator erfolgreich hinterlegt.');
      updateStatus('Die Zwei-Faktor-Authentifizierung ist aktiv.', 'success');
      pendingSetup = null;
      setTimeout(() => {
        hideAuthenticatorSetup();
        fetchSecurityStatus();
      }, 1500);
    } catch (err) {
      console.error('Bestätigung fehlgeschlagen', err);
      showError('Der Code konnte nicht überprüft werden.');
      updateStatus('Der Code konnte nicht überprüft werden.', 'danger');
    } finally {
      hideElement(loadingEl);
      if (confirmBtn) {
        confirmBtn.disabled = false;
      }
    }
  }

  function defaultHeaders() {
    const token = window.localStorage.getItem('jarvisWebToken');
    return token
      ? {
          'X-Auth-Token': token,
        }
      : {};
  }

  if (confirmBtn) {
    confirmBtn.addEventListener('click', confirmSetup);
  }
  if (closeBtn) {
    closeBtn.addEventListener('click', hideAuthenticatorSetup);
  }
  if (cancelBtn) {
    cancelBtn.addEventListener('click', hideAuthenticatorSetup);
  }
  if (modalBg) {
    modalBg.addEventListener('click', hideAuthenticatorSetup);
  }
  if (codeInput) {
    codeInput.addEventListener('input', () => {
      codeInput.value = codeInput.value.replace(/[^0-9]/g, '').slice(0, 6);
      hideElement(errorEl);
      hideElement(successEl);
    });
    codeInput.addEventListener('keydown', (evt) => {
      if (evt.key === 'Enter') {
        evt.preventDefault();
        confirmBtn?.click();
      }
    });
  }
  if (copyBtn) {
    const originalMarkup = copyBtn.innerHTML;
    copyBtn.dataset.icon = originalMarkup;
    let resetTimer = null;
    copyBtn.addEventListener('click', async () => {
      const secret = secretEl?.textContent?.trim();
      if (!secret || secret === '---') {
        return;
      }
      try {
        await navigator.clipboard.writeText(secret);
        showCopyFeedback(true);
      } catch (err) {
        console.warn('Secret konnte nicht kopiert werden', err);
        showCopyFeedback(false);
      }

      function showCopyFeedback(success) {
        copyBtn.innerHTML = success
          ? '<svg width=\"18\" height=\"18\" viewBox=\"0 0 16 16\" fill=\"currentColor\"><path d=\"M13.485 1.929a.75.75 0 0 1 .075 1.057l-6.5 7.5a.75.75 0 0 1-1.08.05l-3-2.75a.75.75 0 1 1 1.01-1.11l2.418 2.219 5.978-6.893a.75.75 0 0 1 1.099-.073z\"/></svg>'
          : '<svg width=\"18\" height=\"18\" viewBox=\"0 0 16 16\" fill=\"currentColor\"><path d=\"M11.854 4.146a.5.5 0 0 0-.708 0L8 7.293 4.854 4.146a.5.5 0 1 0-.708.708L7.293 8l-3.147 3.146a.5.5 0 0 0 .708.708L8 8.707l3.146 3.147a.5.5 0 0 0 .708-.708L8.707 8l3.147-3.146a.5.5 0 0 0 0-.708z\"/></svg>';
        copyBtn.classList.remove('is-success', 'is-error');
        copyBtn.classList.add(success ? 'is-success' : 'is-error');
        clearTimeout(resetTimer);
        resetTimer = setTimeout(() => {
          copyBtn.innerHTML = copyBtn.dataset.icon || originalMarkup;
          copyBtn.classList.remove('is-success', 'is-error');
        }, 2000);
      }
    });
  }

  if (openBtn) {
    openBtn.addEventListener('click', async () => {
      if (pendingSetup) {
        showAuthenticatorSetup(pendingSetup);
        return;
      }
      if (isFileProtocol) {
        updateStatus('Offline-Modus: Bitte öffne die Weboberfläche über den laufenden JarvisCore-Server.', 'warning');
        return;
      }
      await fetchSecurityStatus();
      if (pendingSetup) {
        showAuthenticatorSetup(pendingSetup);
      } else {
        updateStatus('Keine Einrichtung erforderlich – die Zwei-Faktor-Authentifizierung ist aktiv.', 'success');
      }
    });
  }

  function appendFallbackMessage(container, uri, secret) {
    const fallback = document.createElement('div');
    fallback.className = 'qr-fallback';

    const infoText = document.createElement('span');
    infoText.textContent = 'QRCode konnte nicht erzeugt werden.';
    fallback.appendChild(infoText);

    if (uri) {
      const link = document.createElement('a');
      link.href = uri;
      link.target = '_blank';
      link.rel = 'noreferrer';
      link.textContent = 'QR-Code extern öffnen';
      fallback.appendChild(link);
    }

    if (secret) {
      const secretWrapper = document.createElement('small');
      secretWrapper.textContent = 'Geheimschlüssel: ';
      const codeNode = document.createElement('code');
      codeNode.textContent = secret;
      secretWrapper.appendChild(codeNode);
      fallback.appendChild(secretWrapper);
    }

    container.appendChild(fallback);
  }

  function resetAuthenticatorForm() {
    if (codeInput) {
      codeInput.value = '';
    }
    hideElement(loadingEl);
    hideElement(errorEl);
    hideElement(successEl);
    if (confirmBtn) {
      confirmBtn.disabled = false;
    }
    if (copyBtn && copyBtn.dataset) {
      copyBtn.innerHTML = copyBtn.dataset.icon || copyBtn.innerHTML;
      copyBtn.classList.remove('is-success', 'is-error');
    }
  }

  function showError(message) {
    if (!errorEl) {
      alert(message);
      return;
    }
    errorEl.textContent = message;
    hideElement(successEl);
    showElement(errorEl);
  }

  function showSuccess(message) {
    if (!successEl) {
      console.info(message);
      return;
    }
    successEl.textContent = message;
    hideElement(errorEl);
    showElement(successEl);
  }

  function hideElement(element) {
    if (element && !element.classList.contains('is-hidden')) {
      element.classList.add('is-hidden');
    }
  }

  function showElement(element) {
    if (element) {
      element.classList.remove('is-hidden');
    }
  }

  function updateStatus(message, tone = 'info') {
    if (!statusEl) {
      return;
    }
    const toneMap = {
      info: 'is-info',
      success: 'is-success',
      warning: 'is-warning',
      danger: 'is-danger',
    };
    statusEl.textContent = message;
    statusEl.classList.remove('is-info', 'is-success', 'is-warning', 'is-danger');
    if (tone === 'hidden') {
      statusEl.classList.add('is-hidden');
      statusEl.dataset.state = 'hidden';
      return;
    }
    statusEl.classList.remove('is-hidden');
    statusEl.classList.add(toneMap[tone] || toneMap.info);
    statusEl.dataset.state = tone;
  }

  fetchSecurityStatus();
  setInterval(fetchSecurityStatus, 15000);

  document.addEventListener('keydown', (evt) => {
    if (evt.key === 'Escape' && modal?.classList.contains('is-active')) {
      hideAuthenticatorSetup();
    }
  });
});
