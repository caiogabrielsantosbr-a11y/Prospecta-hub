/*******************************************************
 * PROSPECTAHUB — AppScript Integration v2
 * Controle completo via API (doPost/doGet)
 * + Sidebar local para operação manual
 *******************************************************/

/*******************************************************
 * CONFIGURAÇÕES PADRÃO (overrideáveis via /configure)
 *******************************************************/
const RECIPIENT_COL  = "EMAIL";
const EMAIL_SENT_COL = "STATUS";

const DEFAULT_DAILY_LIMIT       = 80;
const DEFAULT_HOURLY_BATCH_SIZE = 20;
const DEFAULT_MIN_HOUR          = 8;
const DEFAULT_MAX_HOUR          = 16;

/*******************************************************
 * MENU E UI
 *******************************************************/
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("📨 Prospecta HUB")
    .addItem("Abrir Painel", "openPanel")
    .addToUi();
}

function openPanel() {
  const html = HtmlService.createHtmlOutputFromFile("Sidebar")
    .setTitle("Prospecta HUB")
    .setWidth(500);
  SpreadsheetApp.getUi().showSidebar(html);
}

/*******************************************************
 * HELPERS
 *******************************************************/
function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function getProps() {
  return PropertiesService.getScriptProperties();
}

/*******************************************************
 * API ENTRY POINTS
 *******************************************************/

/**
 * POST /exec — dispatcher de ações
 * Payload: { action: string, ...params }
 *
 * Actions disponíveis:
 *   add_leads    — envia leads para a planilha
 *   configure    — reconfigura limites e horários
 *   schedule     — ativa/desativa agendamento
 *   trigger_send — dispara envio imediato
 *   stop         — para o agendamento
 *   clear        — limpa a lista de leads
 *   get_stats    — retorna stats completos
 *   get_settings — retorna configurações atuais
 */
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const action = payload.action || 'add_leads';

    switch (action) {
      case 'add_leads':    return handleAddLeads(payload);
      case 'configure':    return handleConfigure(payload);
      case 'schedule':     return handleSchedule(payload);
      case 'trigger_send': return handleTriggerSend(payload);
      case 'stop':         return handleStop();
      case 'clear':        return handleClear();
      case 'get_stats':    return handleGetStats();
      case 'get_settings':      return handleGetSettings();
      case 'configure_report':  return handleConfigureReport(payload);
      case 'get_report_config': return handleGetReportConfig();
      default:
        return jsonResponse({ success: false, error: 'Ação desconhecida: ' + action });
    }
  } catch (err) {
    return jsonResponse({ success: false, error: err.message });
  }
}

/**
 * GET /exec — retorna stats/settings OU executa ação via ?payload=
 * Usado pelo frontend para contornar CORS (POST aciona preflight, GET não).
 * Params:
 *   ?action=stats|settings|report_config  — leitura (padrão: stats)
 *   ?payload={"action":"configure",...}   — qualquer ação de escrita
 */
function doGet(e) {
  // Ação de escrita enviada como GET para evitar CORS preflight
  if (e.parameter && e.parameter.payload) {
    try {
      const fakeEvent = { postData: { contents: e.parameter.payload } };
      return doPost(fakeEvent);
    } catch (err) {
      return jsonResponse({ success: false, error: 'payload inválido: ' + err.message });
    }
  }

  const action = (e.parameter && e.parameter.action) || 'stats';
  switch (action) {
    case 'settings':      return handleGetSettings();
    case 'report_config': return handleGetReportConfig();
    default:              return handleGetStats();
  }
}

/*******************************************************
 * HANDLERS
 *******************************************************/

/**
 * add_leads — adiciona leads à planilha com deduplicação
 * Payload: { leads: [{EMPRESA, EMAIL, TELEFONE, CIDADE, WEBSITE}] }
 * Retorna: { success, rows_added, skipped }
 */
function handleAddLeads(payload) {
  const leads = payload.leads || [];
  if (!leads.length) {
    return jsonResponse({ success: false, error: 'Nenhum lead recebido' });
  }

  const sheet = SpreadsheetApp.getActiveSheet();
  const HEADERS = ['EMPRESA', 'EMAIL', 'TELEFONE', 'CIDADE', 'WEBSITE', 'STATUS'];

  // Ensure header exists
  if (sheet.getLastRow() === 0 || sheet.getLastColumn() === 0) {
    sheet.appendRow(HEADERS);
    SpreadsheetApp.flush();
  }
  
  // Verify header structure (ensure all 6 columns exist in correct order)
  const existingHeaders = sheet.getRange(1, 1, 1, 6).getValues()[0];
  let headerNeedsUpdate = false;
  for (let i = 0; i < HEADERS.length; i++) {
    if (existingHeaders[i] !== HEADERS[i]) {
      headerNeedsUpdate = true;
      break;
    }
  }
  
  if (headerNeedsUpdate) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    SpreadsheetApp.flush();
  }

  // Collect existing emails for deduplication (column 2 = EMAIL)
  const existingEmails = new Set();
  const lastRow = sheet.getLastRow();
  if (lastRow > 1) {
    sheet.getRange(2, 2, lastRow - 1, 1).getValues()
      .forEach(r => { if (r[0]) existingEmails.add(String(r[0]).toLowerCase().trim()); });
  }

  // Filter only new leads (email not duplicated)
  const newLeads = leads.filter(lead => {
    const email = String(lead.EMAIL || '').toLowerCase().trim();
    return email && !existingEmails.has(email);
  });

  if (!newLeads.length) {
    return jsonResponse({ 
      success: true, 
      rows_added: 0, 
      skipped: leads.length, 
      message: 'Todos os leads já existem na planilha' 
    });
  }

  // Batch write — map fields to fixed column order
  const rows = newLeads.map(lead => [
    lead.EMPRESA  || '',  // Column 1
    lead.EMAIL    || '',  // Column 2
    lead.TELEFONE || '',  // Column 3
    lead.CIDADE   || '',  // Column 4
    lead.WEBSITE  || '',  // Column 5
    '',                   // Column 6 (STATUS)
  ]);

  const startRow = sheet.getLastRow() + 1;
  sheet.getRange(startRow, 1, rows.length, HEADERS.length).setValues(rows);
  SpreadsheetApp.flush();

  return jsonResponse({ 
    success: true, 
    rows_added: newLeads.length, 
    skipped: leads.length - newLeads.length 
  });
}

/**
 * configure — reconfigura parâmetros de envio
 * Payload: {
 *   daily_limit?:       number,
 *   hourly_batch_size?: number,
 *   min_hour?:          number,
 *   max_hour?:          number,
 *   subject?:           string
 * }
 */
function handleConfigure(payload) {
  const props = getProps();
  const updates = {};

  if (payload.daily_limit !== undefined) {
    props.setProperty('DAILY_LIMIT', String(payload.daily_limit));
    updates.daily_limit = payload.daily_limit;
  }
  if (payload.hourly_batch_size !== undefined) {
    props.setProperty('HOURLY_BATCH_SIZE', String(payload.hourly_batch_size));
    updates.hourly_batch_size = payload.hourly_batch_size;
  }
  if (payload.min_hour !== undefined) {
    props.setProperty('MIN_HOUR', String(payload.min_hour));
    updates.min_hour = payload.min_hour;
  }
  if (payload.max_hour !== undefined) {
    props.setProperty('MAX_HOUR', String(payload.max_hour));
    updates.max_hour = payload.max_hour;
  }
  if (payload.subject !== undefined) {
    props.setProperty('AUTO_SUBJECT', payload.subject);
    updates.subject = payload.subject;
  }
  // SENDER_NAME removido — usa nome padrão da conta Gmail

  return jsonResponse({ success: true, updated: updates });
}

/**
 * schedule — ativa ou reconfigura o agendamento automático
 * Payload: {
 *   active: boolean,
 *   days?:  number[],  // 0=Dom, 1=Seg ... 6=Sab
 *   subject?: string
 * }
 */
function handleSchedule(payload) {
  const props = getProps();

  if (payload.subject) props.setProperty('AUTO_SUBJECT', payload.subject);
  if (payload.days)    props.setProperty('AUTO_DAYS', JSON.stringify(payload.days));

  const active = payload.active === true || payload.active === 'true';
  props.setProperty('AUTO_ACTIVE', String(active));

  deleteTriggers_();

  if (active) {
    ScriptApp.newTrigger('autoExecuteHourly')
      .timeBased()
      .everyHours(1)
      .create();

    props.setProperty('DAILY_SENT_COUNT', '0');
    props.setProperty('LAST_RUN_DATE', new Date().toDateString());

    return jsonResponse({ success: true, message: 'Agendamento ativado (a cada 1 hora)' });
  } else {
    return jsonResponse({ success: true, message: 'Agendamento desativado' });
  }
}

/**
 * trigger_send — dispara envio imediato de um lote
 * Payload: { limit?: number }  — padrão: HOURLY_BATCH_SIZE
 */
function handleTriggerSend(payload) {
  const props = getProps();
  const subject = props.getProperty('AUTO_SUBJECT');
  if (!subject) {
    return jsonResponse({ success: false, error: 'Assunto não configurado. Use a ação configure primeiro.' });
  }

  const batchSize = payload.limit
    ? Number(payload.limit)
    : Number(props.getProperty('HOURLY_BATCH_SIZE') || DEFAULT_HOURLY_BATCH_SIZE);

  const before = countRows_();
  processBatchServerSide_(subject, batchSize);
  const after  = countRows_();

  const sent = before.pending - after.pending;
  return jsonResponse({ success: true, sent, pending_after: after.pending });
}

/**
 * stop — para o agendamento (sem limpar dados)
 */
function handleStop() {
  const props = getProps();
  props.setProperty('AUTO_ACTIVE', 'false');
  deleteTriggers_();
  return jsonResponse({ success: true, message: 'Envios parados' });
}

/**
 * clear — limpa todos os leads da planilha (mantém cabeçalho)
 */
function handleClear() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();
  if (lastRow > 1) {
    sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).clearContent();
  }
  return jsonResponse({ success: true, message: 'Lista limpa' });
}

/**
 * get_stats — retorna estatísticas completas
 */
function handleGetStats() {
  const props   = getProps();
  const rows    = countRows_();
  const dailySent = Number(props.getProperty('DAILY_SENT_COUNT') || 0);
  const dailyLimit = Number(props.getProperty('DAILY_LIMIT') || DEFAULT_DAILY_LIMIT);
  
  // Get Gmail quota with fallback
  let gmailQuota;
  try {
    gmailQuota = MailApp.getRemainingDailyQuota();
  } catch (e) {
    console.error('Erro ao obter cota do Gmail:', e.message);
    gmailQuota = 0;
  }

  return jsonResponse({
    success:        true,
    total:          rows.total,
    sent:           rows.sent,
    pending:        rows.pending,
    errors:         rows.errors,
    quota_gmail:    gmailQuota,
    daily_sent:     dailySent,
    daily_limit:    dailyLimit,
    daily_remaining: Math.max(0, dailyLimit - dailySent),
    schedule_active: props.getProperty('AUTO_ACTIVE') === 'true',
    last_run_date:  props.getProperty('LAST_RUN_DATE') || null,
  });
}

/**
 * get_settings — retorna configurações atuais
 */
function handleGetSettings() {
  const props = getProps();
  return jsonResponse({
    success:           true,
    subject:           props.getProperty('AUTO_SUBJECT')        || '',
    daily_limit:       Number(props.getProperty('DAILY_LIMIT')        || DEFAULT_DAILY_LIMIT),
    hourly_batch_size: Number(props.getProperty('HOURLY_BATCH_SIZE')  || DEFAULT_HOURLY_BATCH_SIZE),
    min_hour:          Number(props.getProperty('MIN_HOUR')            || DEFAULT_MIN_HOUR),
    max_hour:          Number(props.getProperty('MAX_HOUR')            || DEFAULT_MAX_HOUR),
    days:              JSON.parse(props.getProperty('AUTO_DAYS')       || '[]'),
    active:            props.getProperty('AUTO_ACTIVE')          === 'true',
  });
}

/*******************************************************
 * AUTOMAÇÃO HORÁRIA (TRIGGER INTERNO)
 *******************************************************/

function autoExecuteHourly() {
  const props = getProps();

  if (props.getProperty('AUTO_ACTIVE') !== 'true') return;

  const now        = new Date();
  const todayWeek  = now.getDay();
  const allowedDays = JSON.parse(props.getProperty('AUTO_DAYS') || '[]');

  if (!allowedDays.includes(todayWeek)) {
    console.log("Hoje não é dia de envio configurado.");
    return;
  }

  const currentHour = now.getHours();
  const minHour = Number(props.getProperty('MIN_HOUR') || DEFAULT_MIN_HOUR);
  const maxHour = Number(props.getProperty('MAX_HOUR') || DEFAULT_MAX_HOUR);

  if (currentHour < minHour || currentHour >= maxHour) {
    console.log(`Fora do horário (${currentHour}h). Limite: ${minHour}h–${maxHour}h`);
    return;
  }

  const todayStr   = now.toDateString();
  const lastRun    = props.getProperty('LAST_RUN_DATE');
  let dailyCount   = Number(props.getProperty('DAILY_SENT_COUNT') || 0);
  const dailyLimit = Number(props.getProperty('DAILY_LIMIT') || DEFAULT_DAILY_LIMIT);
  const batchSize  = Number(props.getProperty('HOURLY_BATCH_SIZE') || DEFAULT_HOURLY_BATCH_SIZE);

  if (lastRun !== todayStr) {
    dailyCount = 0;
    props.setProperty('LAST_RUN_DATE', todayStr);
    props.setProperty('DAILY_SENT_COUNT', '0');
  }

  if (dailyCount >= dailyLimit) {
    console.log(`Meta diária atingida (${dailyCount}/${dailyLimit}).`);
    return;
  }

  const subject = props.getProperty('AUTO_SUBJECT');
  if (!subject) return;

  const remaining  = dailyLimit - dailyCount;
  const batchToRun = Math.min(remaining, batchSize);

  console.log(`Lote horário: ${batchToRun} emails. Dia: ${dailyCount}/${dailyLimit}`);
  processBatchServerSide_(subject, batchToRun);
}

/*******************************************************
 * MOTOR DE ENVIO
 *******************************************************/

function processBatchServerSide_(subjectLine, maxEmails) {
  const sheet   = SpreadsheetApp.getActiveSheet();
  const data    = sheet.getDataRange().getDisplayValues();
  const headers = data[0];
  const props   = getProps();

  const emailIdx  = headers.indexOf(RECIPIENT_COL);
  const statusIdx = headers.indexOf(EMAIL_SENT_COL);

  let template;
  try {
    template = getGmailTemplateFromDrafts_(subjectLine);
  } catch (e) {
    console.error("Template não encontrado: " + e.message);
    return;
  }

  let sentInThisBatch = 0;
  let currentDailyCount = Number(props.getProperty('DAILY_SENT_COUNT') || 0);

  for (let i = 1; i < data.length; i++) {
    if (sentInThisBatch >= maxEmails) break;

    if (data[i][emailIdx] && data[i][statusIdx] === '') {
      const rowData = data[i];
      const rowObj  = headers.reduce((obj, header, k) => { obj[header] = rowData[k]; return obj; }, {});

      try {
        const msgObj = fillInTemplateFromObject_(template.message, rowObj);

        GmailApp.sendEmail(
          rowObj[RECIPIENT_COL],
          msgObj.subject,
          msgObj.text,
          {
            htmlBody:     msgObj.html,
            attachments:  template.attachments,
            inlineImages: template.inlineImages,
          }
        );

        sheet.getRange(i + 1, statusIdx + 1).setValue('OK_AUTO');
        SpreadsheetApp.flush();

        sentInThisBatch++;
        currentDailyCount++;
        props.setProperty('DAILY_SENT_COUNT', String(currentDailyCount));

        const delay = Math.floor(Math.random() * 5000) + 10000;
        Utilities.sleep(delay);

      } catch (e) {
        const errorMsg = e.message.toLowerCase();
        sheet.getRange(i + 1, statusIdx + 1).setValue('ERRO: ' + e.message);

        if (errorMsg.includes('limit') || errorMsg.includes('quota') || errorMsg.includes('many times')) {
          console.log('Cota atingida ou bloqueio. Parando.');
          break;
        }
      }
    }
  }

  // Relatório de conclusão: disparar quando não houver mais pendentes
  if (countRows_().pending === 0) {
    sendCompletionReport_();
  }
}

/*******************************************************
 * ENVIO MANUAL (CHAMADO PELO SIDEBAR)
 *******************************************************/

function getPendingEmails(limit) {
  const sheet    = SpreadsheetApp.getActiveSheet();
  const data     = sheet.getDataRange().getDisplayValues();
  const headers  = data[0];
  const emailIdx = headers.indexOf(RECIPIENT_COL);
  const statusIdx = headers.indexOf(EMAIL_SENT_COL);
  const maxEmails = limit ? Number(limit) : 9999;
  const pending   = [];

  for (let i = 1; i < data.length; i++) {
    if (pending.length >= maxEmails) break;
    if (data[i][emailIdx] && data[i][statusIdx] === '') {
      pending.push(i + 1);
    }
  }

  return { total: pending.length, rows: pending, quota: MailApp.getRemainingDailyQuota() };
}

function sendSingleEmail(rowIndex, config) {
  const sheet   = SpreadsheetApp.getActiveSheet();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const rowData = sheet.getRange(rowIndex, 1, 1, sheet.getLastColumn()).getDisplayValues()[0];
  const rowObj  = headers.reduce((obj, header, i) => { obj[header] = rowData[i]; return obj; }, {});
  const recipient  = rowObj[RECIPIENT_COL];
  const sentIndex  = headers.indexOf(EMAIL_SENT_COL) + 1;

  try {
    if (!recipient) return { success: false, error: 'Email vazio' };
    const template = getGmailTemplateFromDrafts_(config.subjectLine);
    const msgObj   = fillInTemplateFromObject_(template.message, rowObj);

    GmailApp.sendEmail(recipient, msgObj.subject, msgObj.text, {
      htmlBody:     msgObj.html,
      attachments:  template.attachments,
      inlineImages: template.inlineImages,
    });

    sheet.getRange(rowIndex, sentIndex).setValue('OK');
    const delay = randomDelay(Number(config.minDelay), Number(config.maxDelay));
    Utilities.sleep(delay);

    return { success: true, email: recipient };
  } catch (e) {
    sheet.getRange(rowIndex, sentIndex).setValue('ERRO: ' + e.message);
    return { success: false, email: recipient, error: e.message };
  }
}

/*******************************************************
 * FUNÇÕES PARA O SIDEBAR LOCAL
 *******************************************************/

function getQuotaOnly() {
  return MailApp.getRemainingDailyQuota();
}

function getWebhookUrl() {
  return ScriptApp.getService().getUrl();
}

function getStoredSettings() {
  const props = getProps();
  return {
    subject:           props.getProperty('AUTO_SUBJECT')        || '',
    hour:              props.getProperty('MIN_HOUR')            || '8',
    days:              props.getProperty('AUTO_DAYS')           || '[]',
    active:            props.getProperty('AUTO_ACTIVE')         === 'true',
    daily_limit:       props.getProperty('DAILY_LIMIT')         || '80',
    hourly_batch_size: props.getProperty('HOURLY_BATCH_SIZE')   || '20',
    max_hour:          props.getProperty('MAX_HOUR')            || '16',
  };
}

function saveSchedule(config) {
  const props = getProps();

  if (config.subject)           props.setProperty('AUTO_SUBJECT',        config.subject);
  if (config.days)              props.setProperty('AUTO_DAYS',            JSON.stringify(config.days));
  if (config.daily_limit)       props.setProperty('DAILY_LIMIT',          String(config.daily_limit));
  if (config.hourly_batch_size) props.setProperty('HOURLY_BATCH_SIZE',    String(config.hourly_batch_size));
  if (config.min_hour)          props.setProperty('MIN_HOUR',             String(config.min_hour));
  if (config.max_hour)          props.setProperty('MAX_HOUR',             String(config.max_hour));

  const active = config.active === true || config.active === 'true';
  props.setProperty('AUTO_ACTIVE', String(active));

  deleteTriggers_();

  if (active) {
    ScriptApp.newTrigger('autoExecuteHourly').timeBased().everyHours(1).create();
    props.setProperty('DAILY_SENT_COUNT', '0');
    props.setProperty('LAST_RUN_DATE', new Date().toDateString());
    return `✅ Agendado! O robô verifica a cada 1 hora (${config.min_hour || 8}h–${config.max_hour || 16}h).`;
  } else {
    return '🛑 Agendamento desativado.';
  }
}

function clearData() {
  const result = handleClear();
  const obj    = JSON.parse(result.getContent());
  return obj.success ? '✅ Lista limpa com sucesso! (Cabeçalho mantido)' : 'Erro: ' + obj.message;
}

function sendTest(config) {
  try {
    const template = getGmailTemplateFromDrafts_(config.subjectLine);
    GmailApp.sendEmail(config.to, template.message.subject, template.message.text, {
      htmlBody: template.message.html,
      attachments:  template.attachments,
      inlineImages: template.inlineImages,
    });
    return '✅ Teste enviado com sucesso!';
  } catch (e) { throw new Error(e.message); }
}

/*******************************************************
 * RELATÓRIO DIÁRIO
 *******************************************************/

/**
 * configure_report — configura relatório de conclusão por email
 * Payload: { recipient_email?, enabled? }
 */
function handleConfigureReport(payload) {
  const props = getProps();

  if (payload.recipient_email !== undefined)
    props.setProperty('REPORT_EMAIL', payload.recipient_email);
  if (payload.enabled !== undefined)
    props.setProperty('REPORT_ENABLED', String(payload.enabled === true || payload.enabled === 'true'));

  // Remove trigger de hora fixa (legado)
  deleteTriggerByName_('sendDailyReport');

  const enabled = props.getProperty('REPORT_ENABLED') === 'true';
  return jsonResponse({
    success:      true,
    report_enabled: enabled,
    report_email: props.getProperty('REPORT_EMAIL') || '',
  });
}

/**
 * get_report_config — retorna configuração atual do relatório
 */
function handleGetReportConfig() {
  const props = getProps();
  return jsonResponse({
    success:        true,
    report_enabled: props.getProperty('REPORT_ENABLED') === 'true',
    report_email:   props.getProperty('REPORT_EMAIL')   || '',
  });
}

/**
 * sendCompletionReport_ — disparado internamente ao fim de um lote quando pending === 0
 */
function sendCompletionReport_() {
  const props = getProps();
  if (props.getProperty('REPORT_ENABLED') !== 'true') return;

  const recipient = props.getProperty('REPORT_EMAIL');
  if (!recipient) return;

  const rows      = countRows_();
  const daily     = Number(props.getProperty('DAILY_SENT_COUNT') || 0);
  const limit     = Number(props.getProperty('DAILY_LIMIT')      || DEFAULT_DAILY_LIMIT);
  const quota     = MailApp.getRemainingDailyQuota();
  const sheetName = SpreadsheetApp.getActiveSpreadsheet().getName();
  const date      = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'dd/MM/yyyy HH:mm');

  const html = `
    <div style="font-family:Arial,sans-serif;max-width:520px">
      <h2 style="color:#1a73e8">✅ Envios concluídos — ${sheetName}</h2>
      <p><strong>Data/hora:</strong> ${date}</p>
      <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%">
        <tr style="background:#f1f3f4">
          <td><strong>Emails enviados hoje</strong></td>
          <td><strong>${daily}</strong> / ${limit}</td>
        </tr>
        <tr><td>Total na planilha</td><td>${rows.total}</td></tr>
        <tr><td>Pendentes</td><td>${rows.pending}</td></tr>
        <tr><td>Erros</td><td>${rows.errors}</td></tr>
        <tr style="background:#f1f3f4"><td>Cota Gmail restante</td><td>${quota}</td></tr>
      </table>
      <p style="color:#999;font-size:11px;margin-top:16px">
        Enviado automaticamente pelo Prospecta HUB
      </p>
    </div>
  `;

  GmailApp.sendEmail(
    recipient,
    `✅ Envios concluídos — ${sheetName} (${date})`,
    `Envios concluídos em ${date}: ${daily}/${limit} enviados, ${rows.pending} pendentes, cota Gmail ${quota}.`,
    { htmlBody: html }
  );
}

/*******************************************************
 * UTILITÁRIOS INTERNOS
 *******************************************************/

function countRows_() {
  const sheet     = SpreadsheetApp.getActiveSheet();
  const data      = sheet.getDataRange().getDisplayValues();
  if (data.length <= 1) return { total: 0, sent: 0, pending: 0, errors: 0 };

  const headers   = data[0];
  const statusIdx = headers.indexOf(EMAIL_SENT_COL);
  let sent = 0, pending = 0, errors = 0;

  for (let i = 1; i < data.length; i++) {
    const s = statusIdx >= 0 ? data[i][statusIdx] : '';
    if (s === 'OK' || s === 'OK_AUTO') sent++;
    else if (s.startsWith('ERRO')) errors++;
    else pending++;
  }

  return { total: data.length - 1, sent, pending, errors };
}

function deleteTriggers_() {
  deleteTriggerByName_('autoExecuteHourly');
  deleteTriggerByName_('autoExecute');
}

function deleteTriggerByName_(funcName) {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === funcName) ScriptApp.deleteTrigger(t);
  });
}

function randomDelay(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function getGmailTemplateFromDrafts_(subject_line) {
  const drafts = GmailApp.getDrafts();
  const draft  = drafts.find(d => d.getMessage().getSubject() === subject_line);
  if (!draft) throw new Error("Rascunho '" + subject_line + "' não encontrado no Gmail.");

  const msg         = draft.getMessage();
  const attachments = msg.getAttachments({ includeInlineImages: false });
  const inlineImgs  = msg.getAttachments({ includeInlineImages: true, includeAttachments: false });
  const htmlBody    = msg.getBody();

  const imgMap = {};
  inlineImgs.forEach(img => imgMap[img.getName()] = img);

  const inlineImagesObj = {};
  const regex = /<img.*?src="cid:(.*?)".*?alt="(.*?)"[^>]+>/g;
  let match;
  while ((match = regex.exec(htmlBody)) !== null) {
    inlineImagesObj[match[1]] = imgMap[match[2]];
  }

  return {
    message:      { subject: subject_line, text: msg.getPlainBody(), html: htmlBody },
    attachments:  attachments,
    inlineImages: inlineImagesObj,
  };
}

function fillInTemplateFromObject_(template, data) {
  let str = JSON.stringify(template);
  str = str.replace(/{{[^{}]+}}/g, key => {
    const name = key.replace(/[{}]+/g, '').trim();
    return escapeData_(data[name] || '');
  });
  return JSON.parse(str);
}

function escapeData_(str) {
  return String(str).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '<br>');
}
