<!DOCTYPE html>
<html lang="${(locale.currentLanguageTag)!'en'}">
<head>
  <meta charset="utf-8">
  <meta name="viewport"
        content="width=device-width, initial-scale=1">
  <title>${(realm.displayName)!'MeepleTime'} &#8212; Sign in</title>
  <link
    rel="stylesheet"
    href="${url.resourcesPath}/css/login.css"
  >
</head>
<body>

<div class="mt-backdrop" aria-hidden="true">
  <svg class="mt-grid" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <pattern
        id="hexgrid"
        width="40"
        height="40"
        patternUnits="userSpaceOnUse"
      >
        <path
          d="M20 0 L40 20 L20 40 L0 20 Z"
          fill="none"
          stroke="#ffb5a1"
          stroke-width="0.75"
          opacity="0.06"
        />
      </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#hexgrid)"/>
  </svg>
</div>

<div class="mt-wrap">

  <div class="mt-card">
    <div class="mt-glow" aria-hidden="true"></div>
    <div class="mt-content">

      <header class="mt-brand">
        <span class="mt-brand-name">MeepleTime</span>
      </header>

      <div class="mt-intro">
        <h1 class="mt-title">
          Gather your party
        </h1>
      </div>

      <#if message?has_content
        && !messagesPerField.existsError('username', 'password')>
        <div
          class="mt-alert mt-alert-${message.type}"
          role="alert"
        >
          ${kcSanitize(message.summary)?no_esc}
        </div>
      </#if>

      <#if realm.password>
        <form
          id="kc-form-login"
          class="mt-form"
          action="${url.loginAction}"
          method="post"
        >
          <div class="mt-field">
            <label for="username" class="mt-label">
              <#if realm.loginWithEmailAllowed
                && !realm.registrationEmailAsUsername>
                ${msg("usernameOrEmail")}
              <#elseif realm.loginWithEmailAllowed>
                ${msg("email")}
              <#else>
                ${msg("username")}
              </#if>
            </label>
            <input
              id="username"
              class="mt-input"
              name="username"
              value="${(login.username!'')}"
              type="text"
              autofocus
              autocomplete="username"
              aria-invalid="\
${messagesPerField.existsError('username')?c}"
            />
            <#if messagesPerField.existsError('username')>
              <span class="mt-field-error" aria-live="polite">
                ${kcSanitize(
                  messagesPerField.get('username'))?no_esc}
              </span>
            </#if>
          </div>

          <div class="mt-field">
            <div class="mt-label-row">
              <label for="password" class="mt-label">
                ${msg("password")}
              </label>
              <#if realm.resetPasswordAllowed>
                <a
                  class="mt-link-secondary"
                  href="${url.loginResetCredentialsUrl}"
                >
                  ${msg("doForgotPassword")}
                </a>
              </#if>
            </div>
            <input
              id="password"
              class="mt-input"
              name="password"
              type="password"
              autocomplete="current-password"
              aria-invalid="\
${messagesPerField.existsError('password')?c}"
            />
            <#if messagesPerField.existsError('password')>
              <span class="mt-field-error" aria-live="polite">
                ${kcSanitize(
                  messagesPerField.get('password'))?no_esc}
              </span>
            </#if>
          </div>

          <#if realm.rememberMe>
            <label class="mt-remember">
              <input
                id="rememberMe"
                name="rememberMe"
                type="checkbox"
                <#if login.rememberMe??>checked</#if>
              />
              <span>${msg("rememberMe")}</span>
            </label>
          </#if>

          <#if auth.selectedCredential?has_content>
            <input
              type="hidden"
              id="id-hidden-input"
              name="credentialId"
              value="${auth.selectedCredential}"
            />
          </#if>

          <button class="mt-submit" name="login" type="submit">
            ${msg("doLogIn")}
          </button>
        </form>
      </#if>

      <#if social.providers?? && social.providers?size gt 0>
        <div class="mt-divider">
          <span>${msg("identity-provider-login-label")}</span>
        </div>
        <div class="mt-social-grid" id="kc-social-providers">
          <#list social.providers as p>
            <a
              id="social-${p.alias}"
              class="mt-social"
              href="${p.loginUrl}"
            >
              <span>${p.displayName!p.alias}</span>
            </a>
          </#list>
        </div>
      </#if>

    </div>
  </div>

  <footer class="mt-footer" aria-label="Auxiliary actions">
    <#if realm.password && realm.registrationAllowed
      && !registrationDisabled??>
      <div class="mt-footer-left">
        <span>${msg("noAccount")}</span>
          <a href="${url.registrationUrl}">${msg("doRegister")}</a>
      </div>
    </#if>
    <div class="mt-footer-right">
      <span>&#169; 2026 MeepleTime</span>
    </div>
  </footer>

</div>

</body>
</html>
