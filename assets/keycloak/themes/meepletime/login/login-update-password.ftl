<!DOCTYPE html>
<html lang="${(locale.currentLanguageTag)!'en'}">
<head>
  <meta charset="utf-8">
  <meta name="viewport"
        content="width=device-width, initial-scale=1">
  <title>
    ${(realm.displayName)!'MeepleTime'} &#8212; New password
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
        <h1 class="mt-title">Set your new password</h1>
      </div>

      <#if message?has_content
        && !messagesPerField.existsError('password',
              'password-confirm')>
        <div
          class="mt-alert mt-alert-${message.type}"
          role="alert"
        >
          ${kcSanitize(message.summary)?no_esc}
        </div>
      </#if>

      <form
        id="kc-passwd-update-form"
        class="mt-form"
        action="${url.loginAction}"
        method="post"
      >
        <input
          type="text"
          id="username"
          name="username"
          value="${(username)!''}"
          autocomplete="username"
          readonly
          style="display:none"
        />
        <input
          type="password"
          id="password-new"
          name="password-new"
          autocomplete="new-password"
          style="display:none"
        />

        <div class="mt-field">
          <label for="password" class="mt-label">
            ${msg("passwordNew")}
          </label>
          <input
            id="password"
            class="mt-input"
            name="password"
            type="password"
            autofocus
            autocomplete="new-password"
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

        <div class="mt-field">
          <label for="password-confirm" class="mt-label">
            ${msg("passwordConfirm")}
          </label>
          <input
            id="password-confirm"
            class="mt-input"
            name="password-confirm"
            type="password"
            autocomplete="new-password"
            aria-invalid="\
${messagesPerField.existsError('password-confirm')?c}"
          />
          <#if messagesPerField.existsError('password-confirm')>
            <span class="mt-field-error" aria-live="polite">
              ${kcSanitize(messagesPerField.get(
                'password-confirm'))?no_esc}
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
    <div class="mt-footer-right">
      <span>&#169; 2026 MeepleTime</span>
    </div>
  </footer>

</div>

</body>
</html>
