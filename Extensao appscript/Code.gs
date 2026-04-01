/*******************************************************
 * CONFIGURAÇÕES GERAIS
 *******************************************************/
const RECIPIENT_COL  = "EMAIL";
const EMAIL_SENT_COL = "STATUS";

// --- ESTRATÉGIA "CONTA-GOTAS" (MICRO-LOTES) ---
const DAILY_LIMIT = 80;       // Meta total do dia
const HOURLY_BATCH_SIZE = 20; // Envia apenas 15 por hora (Super Seguro)
const MIN_HOUR = 8;           // Começa as 08:00 da manhã
const MAX_HOUR = 16;          // Para as 16:00 (4h da tarde)

/*******************************************************
 * MENU E UI
 *******************************************************/
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("📨 Enviar Email")
    .addItem("Abrir Painel", "openPanel")
    .addToUi();
}

function openPanel() {
  const html = HtmlService.createHtmlOutputFromFile("Sidebar")
    .setTitle("Prospecção Email PRO")
    .setWidth(500); 
  SpreadsheetApp.getUi().showSidebar(html);
}

/*******************************************************
 * FUNÇÕES DE API (COTA E DADOS)
 *******************************************************/
function getQuotaOnly() {
  return MailApp.getRemainingDailyQuota();
}

function getStoredSettings() {
  const props = PropertiesService.getScriptProperties();
  return {
    subject: props.getProperty('AUTO_SUBJECT') || '',
    hour: props.getProperty('AUTO_HOUR') || '8', 
    days: props.getProperty('AUTO_DAYS') || '[]',
    active: props.getProperty('AUTO_ACTIVE') === 'true'
  };
}

/*******************************************************
 * 1. LÓGICA DE AGENDAMENTO (HORÁRIO INTELIGENTE)
 *******************************************************/

function saveSchedule(config) {
  const props = PropertiesService.getScriptProperties();
  
  props.setProperty('AUTO_SUBJECT', config.subject);
  props.setProperty('AUTO_DAYS', JSON.stringify(config.days));
  props.setProperty('AUTO_ACTIVE', config.active); 
  
  deleteTriggers_(); // Limpa gatilhos antigos

  if (config.active === true || config.active === "true") {
    // --- GATILHO DE 1 EM 1 HORA ---
    ScriptApp.newTrigger('autoExecuteHourly')
      .timeBased()
      .everyHours(1) 
      .create();
      
    // Reseta o contador do dia ao ativar
    props.setProperty('DAILY_SENT_COUNT', '0');
    props.setProperty('LAST_RUN_DATE', new Date().toDateString());

    return `✅ Agendado! O robô verificará a cada 1 hora (entre ${MIN_HOUR}h e ${MAX_HOUR}h).`;
  } else {
    return "🛑 Agendamento desativado com sucesso.";
  }
}

function deleteTriggers_() {
  const triggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < triggers.length; i++) {
    const func = triggers[i].getHandlerFunction();
    if (func === 'autoExecuteHourly' || func === 'autoExecute') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
}

/**
 * FUNÇÃO QUE RODA DE HORA EM HORA (SERVER-SIDE)
 */
function autoExecuteHourly() {
  const props = PropertiesService.getScriptProperties();
  
  // 1. Verifica se está ativo
  if (props.getProperty('AUTO_ACTIVE') !== 'true') return;

  // 2. Verifica Dia da Semana
  const now = new Date();
  const todayWeek = now.getDay(); // 0=Dom, 1=Seg...
  const allowedDays = JSON.parse(props.getProperty('AUTO_DAYS') || '[]');
  
  if (!allowedDays.includes(todayWeek)) {
    console.log("Hoje não é dia de envio configurado.");
    return;
  }

  // 3. Verifica Horário Comercial (AGORA ATÉ AS 16h)
  const currentHour = now.getHours();
  // Se for antes das 8 ou depois/igual a 16 (4h da tarde), não roda.
  if (currentHour < MIN_HOUR || currentHour >= MAX_HOUR) {
    console.log(`Fora do horário comercial (${currentHour}h). O robô está dormindo...`);
    return;
  }

  // 4. Controle de Cota Diária (Reset e Verificação)
  const todayDateStr = now.toDateString();
  const lastRunDate = props.getProperty('LAST_RUN_DATE');
  let dailyCount = Number(props.getProperty('DAILY_SENT_COUNT') || 0);

  if (lastRunDate !== todayDateStr) {
    console.log("Novo dia detectado. Zerando contador diário.");
    dailyCount = 0;
    props.setProperty('LAST_RUN_DATE', todayDateStr);
    props.setProperty('DAILY_SENT_COUNT', '0');
  }

  if (dailyCount >= DAILY_LIMIT) {
    console.log(`Meta diária atingida (${dailyCount}/${DAILY_LIMIT}). Até amanhã!`);
    return;
  }

  const subject = props.getProperty('AUTO_SUBJECT');
  if (!subject) return;

  // 5. Calcula lote
  let remaining = DAILY_LIMIT - dailyCount;
  let batchToRun = Math.min(remaining, HOURLY_BATCH_SIZE);

  console.log(`Iniciando lote horário. Meta Dia: ${dailyCount}/${DAILY_LIMIT}. Lote Atual: ${batchToRun}`);

  // 6. Executa o envio
  processBatchServerSide_(subject, batchToRun); 
}

/**
 * MOTOR DE ENVIO LENTO E SEGURO (DELAY AUMENTADO)
 */
function processBatchServerSide_(subjectLine, maxEmails) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getDisplayValues();
  const headers = data[0];
  const props = PropertiesService.getScriptProperties();
  
  const emailIdx = headers.indexOf(RECIPIENT_COL);
  const statusIdx = headers.indexOf(EMAIL_SENT_COL);
  
  let template;
  try {
    template = getGmailTemplateFromDrafts_(subjectLine);
  } catch (e) {
    console.error("Erro Crítico: " + e.message);
    return;
  }

  let sentInThisBatch = 0;
  let currentDailyCount = Number(props.getProperty('DAILY_SENT_COUNT') || 0);

  for (let i = 1; i < data.length; i++) {
    
    if (sentInThisBatch >= maxEmails) break;

    if (data[i][emailIdx] && data[i][statusIdx] === "") {
      
      const rowData = data[i];
      const rowObj = headers.reduce((obj, header, k) => {
        obj[header] = rowData[k];
        return obj;
      }, {});

      try {
        const msgObj = fillInTemplateFromObject_(template.message, rowObj);
        
        GmailApp.sendEmail(
          rowObj[RECIPIENT_COL],
          msgObj.subject,
          msgObj.text,
          {
            htmlBody: msgObj.html,
            name: "Davi de Araújo", // SEU NOME
            attachments: template.attachments,
            inlineImages: template.inlineImages
          }
        );
        
        // Sucesso
        sheet.getRange(i + 1, statusIdx + 1).setValue("OK_AUTO");
        SpreadsheetApp.flush(); 
        
        sentInThisBatch++;
        currentDailyCount++;
        
        props.setProperty('DAILY_SENT_COUNT', String(currentDailyCount));

        // Delay 10-15s
        const longDelay = Math.floor(Math.random() * 5000) + 10000; 
        console.log(`Email enviado. Total Dia: ${currentDailyCount}. Aguardando ${longDelay}ms...`);
        Utilities.sleep(longDelay);

      } catch (e) {
        const errorMsg = e.message.toLowerCase();
        sheet.getRange(i + 1, statusIdx + 1).setValue("ERRO: " + e.message);
        
        if (errorMsg.includes("limit") || errorMsg.includes("quota") || errorMsg.includes("many times")) {
           console.log("⛔ Cota atingida ou bloqueio temporário. Parando.");
           break;
        }
      }
    }
  }
}

/*******************************************************
 * 2. PREPARAÇÃO DO ENVIO MANUAL (MANTIDO)
 *******************************************************/
function getPendingEmails(limit) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getDisplayValues();
  const headers = data[0];
  const emailIdx = headers.indexOf(RECIPIENT_COL);
  const statusIdx = headers.indexOf(EMAIL_SENT_COL);
  let pendingRows = [];
  const maxEmails = limit ? Number(limit) : 9999; 
   
  for (let i = 1; i < data.length; i++) {
    if (pendingRows.length >= maxEmails) break;
    if (data[i][emailIdx] && data[i][statusIdx] === "") {
      pendingRows.push(i + 1); 
    }
  }
  return { total: pendingRows.length, rows: pendingRows, quota: MailApp.getRemainingDailyQuota() };
}

/*******************************************************
 * 3. AÇÃO: ENVIA UM ÚNICO EMAIL (MANUAL)
 *******************************************************/
function sendSingleEmail(rowIndex, config) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const rowData = sheet.getRange(rowIndex, 1, 1, sheet.getLastColumn()).getDisplayValues()[0];

  const rowObj = headers.reduce((obj, header, i) => {
    obj[header] = rowData[i];
    return obj;
  }, {});

  const recipient = rowObj[RECIPIENT_COL];
  const sentIndex = headers.indexOf(EMAIL_SENT_COL) + 1; 

  try {
    if (!recipient) return { success: false, error: "Email vazio" };
    const template = getGmailTemplateFromDrafts_(config.subjectLine);
    const msgObj = fillInTemplateFromObject_(template.message, rowObj);

    GmailApp.sendEmail(recipient, msgObj.subject, msgObj.text, {
      htmlBody: msgObj.html,
      name: "Davi de Araújo", 
      attachments: template.attachments,
      inlineImages: template.inlineImages
    });

    sheet.getRange(rowIndex, sentIndex).setValue("OK");
    
    // Delay manual
    const delay = randomDelay(Number(config.minDelay), Number(config.maxDelay));
    Utilities.sleep(delay);
    return { success: true, email: recipient };

  } catch (e) {
    sheet.getRange(rowIndex, sentIndex).setValue("ERRO: " + e.message);
    return { success: false, email: recipient, error: e.message };
  }
}

/*******************************************************
 * UTILITÁRIOS
 *******************************************************/
function randomDelay(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }

function sendTest(config) {
  try {
    const template = getGmailTemplateFromDrafts_(config.subjectLine);
    GmailApp.sendEmail(config.to, template.message.subject, template.message.text, {
      htmlBody: template.message.html,
      name: "Teste Sender",
      attachments: template.attachments,
      inlineImages: template.inlineImages
    });
    return "✅ Teste enviado com sucesso!";
  } catch (e) { throw new Error(e.message); }
}

function clearData() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  if (lastRow <= 1) return "A lista já está vazia!";
  sheet.getRange(2, 1, lastRow - 1, lastCol).clearContent();
  return "✅ Lista limpa com sucesso! (Cabeçalho mantido)";
}

/*******************************************************
 * MOTOR DE TEMPLATE (INTERNO)
 *******************************************************/
function getGmailTemplateFromDrafts_(subject_line) {
  const drafts = GmailApp.getDrafts();
  const draft = drafts.find(d => d.getMessage().getSubject() === subject_line);
  if (!draft) throw new Error("Rascunho com assunto '" + subject_line + "' não encontrado.");

  const msg = draft.getMessage();
  const attachments = msg.getAttachments({includeInlineImages: false});
  const inlineImgs = msg.getAttachments({includeInlineImages: true, includeAttachments: false});
  const htmlBody = msg.getBody();

  const imgMap = {};
  inlineImgs.forEach(img => imgMap[img.getName()] = img);

  const inlineImagesObj = {};
  const regex = /<img.*?src="cid:(.*?)".*?alt="(.*?)"[^>]+>/g;
  let match;
  while ((match = regex.exec(htmlBody)) !== null) {
    inlineImagesObj[match[1]] = imgMap[match[2]];
  }

  return {
    message: { subject: subject_line, text: msg.getPlainBody(), html: htmlBody },
    attachments: attachments,
    inlineImages: inlineImagesObj
  };
}

function fillInTemplateFromObject_(template, data) {
  let str = JSON.stringify(template);
  str = str.replace(/{{[^{}]+}}/g, key => {
    const name = key.replace(/[{}]+/g, "").trim();
    return escapeData_(data[name] || "");
  });
  return JSON.parse(str);
}

function escapeData_(str) {
  return String(str).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '<br>');
}

/*******************************************************
 * WEBHOOK: recebe leads do Prospectahub via POST
 * Deploy: Extensões > Apps Script > Implantar > Novo Deploy
 *         Tipo: App da Web, Acesso: Qualquer pessoa
 *******************************************************/
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const leads = payload.leads || [];

    if (!leads.length) {
      return ContentService.createTextOutput(
        JSON.stringify({ success: false, error: 'No leads received' })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    const sheet = SpreadsheetApp.getActiveSheet();

    // Ensure header row exists
    const lastCol = sheet.getLastColumn();
    if (sheet.getLastRow() === 0 || lastCol === 0) {
      sheet.appendRow(['EMPRESA', 'EMAIL', 'TELEFONE', 'CIDADE', 'WEBSITE', 'STATUS']);
    }

    leads.forEach(lead => {
      sheet.appendRow([
        lead.EMPRESA || '',
        lead.EMAIL || '',
        lead.TELEFONE || '',
        lead.CIDADE || '',
        lead.WEBSITE || '',
        '', // STATUS vazio = pronto para envio
      ]);
    });

    SpreadsheetApp.flush();

    return ContentService.createTextOutput(
      JSON.stringify({ success: true, rows_added: leads.length })
    ).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(
      JSON.stringify({ success: false, error: err.message })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Retorna estatísticas da planilha (chamável via GET no webapp URL)
 */
function doGet(e) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const data = sheet.getDataRange().getDisplayValues();
  if (data.length <= 1) {
    return ContentService.createTextOutput(
      JSON.stringify({ total: 0, sent: 0, pending: 0, quota: MailApp.getRemainingDailyQuota() })
    ).setMimeType(ContentService.MimeType.JSON);
  }

  const headers = data[0];
  const statusIdx = headers.indexOf(EMAIL_SENT_COL);
  let sent = 0, pending = 0;

  for (let i = 1; i < data.length; i++) {
    const status = statusIdx >= 0 ? data[i][statusIdx] : '';
    if (status === 'OK' || status === 'OK_AUTO') sent++;
    else pending++;
  }

  return ContentService.createTextOutput(
    JSON.stringify({
      total: data.length - 1,
      sent,
      pending,
      quota: MailApp.getRemainingDailyQuota(),
    })
  ).setMimeType(ContentService.MimeType.JSON);
}