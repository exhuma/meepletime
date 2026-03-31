<!DOCTYPE html>
<html lang="${(locale.currentLanguageTag)!'en'}">
<head>
  <meta charset="utf-8">
  <meta name="viewport"
        content="width=device-width, initial-scale=1">
  <title>
    ${(realm.displayName)!'MeepleTime'} &#8212; Reset password
  </title>
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
        <h1 class="mt-title">Forgot your password?</h1>
        <p class="mt-subtitle">
          Enter your address and we&#8217;ll send a link.
        </p>
      </div>

      <#if message?has_content>
        <div
          class="mt-alert mt-alert-${message.type}"
          role="alert"
        >
          ${kcSanitize(message.summary)?no_esc}
        </div>
      </#if>

      <form
        id="kc-reset-password-form"
        class="mt-form"
        action="${url.loginAction}"
        method="post"
      >
        <div class="mt-field">
          <label for="username" class="mt-label">
            <#if realm.loginWithEmailAllowed
              && realm.registrationEmailAsUsername>
              ${msg("email")}
            <#elseif realm.loginWithEmailAllowed>
              ${msg("usernameOrEmail")}
            <#else>
              ${msg("username")}
            </#if>
          </label>
          <input
            id="username"
            class="mt-input"
            name="username"
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

        <button class="mt-submit" type="submit">
          ${msg("doSubmit")}
        </button>
      </form>

    </div>
  </div>

  <footer class="mt-footer" aria-label="Auxiliary actions">
    <div class="mt-footer-left">
      <a href="${url.loginUrl}">${msg("backToLogin")}</a>
    </div>
    <div class="mt-footer-right">
      <span>&#169; 2026 MeepleTime</span>
    </div>
  </footer>

</div>

</body>
</html>
