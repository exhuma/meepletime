<#macro page
  pageTitle=""
  heroTitle=""
  heroSubtitle=""
  footerLeftHtml=""
  extraHeadHtml=""
>
  <#local mtLang = "en">
  <#if locale?? && locale.currentLanguageTag??>
    <#local mtLang = locale.currentLanguageTag>
  </#if>
  <!DOCTYPE html>
  <html lang="${mtLang}">
  <head>
    <meta charset="utf-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">
    <title>
      ${(realm.displayName)!'MeepleTime'}
      <#if pageTitle?has_content>
        &#8212; ${pageTitle}
      </#if>
    </title>
    <#if extraHeadHtml?has_content>
      ${extraHeadHtml?no_esc}
    </#if>
    <link
      rel="icon"
      type="image/svg+xml"
      href="${url.resourcesPath}/img/favicon.svg"
    >
    <link
      rel="stylesheet"
      href="${url.resourcesPath}/css/login.css"
    >
  </head>
  <body>

  <div class="mt-wrap">

    <div class="mt-card">
      <div class="mt-glow" aria-hidden="true"></div>
      <div class="mt-content">

        <header class="mt-brand">
          <span class="mt-brand-name">MeepleTime</span>
        </header>

        <#if heroTitle?has_content || heroSubtitle?has_content>
          <div class="mt-intro">
            <#if heroTitle?has_content>
              <h1 class="mt-title">${heroTitle}</h1>
            </#if>
            <#if heroSubtitle?has_content>
              <p class="mt-subtitle">${heroSubtitle}</p>
            </#if>
          </div>
        </#if>

        <#nested>

      </div>
    </div>

    <footer class="mt-footer" aria-label="Auxiliary actions">
      <#if footerLeftHtml?has_content>
        <div class="mt-footer-left">
          ${footerLeftHtml?no_esc}
        </div>
      </#if>
      <div class="mt-footer-right">
        <span>&#169; 2026 MeepleTime</span>
      </div>
    </footer>

  </div>

  </body>
  </html>
</#macro>

<#macro messageAlert
  role="alert"
  forceType=""
  excludedFields=[]
>
  <#if message?has_content>
    <#local mtShowMessage = true>
    <#if messagesPerField??>
      <#list excludedFields as fieldName>
        <#if messagesPerField.existsError(fieldName)>
          <#local mtShowMessage = false>
        </#if>
      </#list>
    </#if>
    <#if mtShowMessage>
      <#local mtAlertType = forceType>
      <#if !mtAlertType?has_content>
        <#local mtAlertType = message.type>
      </#if>
      <div
        class="mt-alert mt-alert-${mtAlertType}"
        role="${role}"
      >
        ${kcSanitize(message.summary)?no_esc}
      </div>
    </#if>
  </#if>
</#macro>

<#macro fieldError name>
  <#if messagesPerField?? && messagesPerField.existsError(name)>
    <span class="mt-field-error" aria-live="polite">
      ${kcSanitize(messagesPerField.get(name))?no_esc}
    </span>
  </#if>
</#macro>

<#macro submitLink href label>
  <a class="mt-submit mt-submit-link" href="${href}">
    ${label}
  </a>
</#macro>