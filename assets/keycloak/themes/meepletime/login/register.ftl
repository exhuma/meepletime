<!DOCTYPE html>
<html lang="${(locale.currentLanguageTag)!'en'}">
<head>
  <meta charset="utf-8">
  <meta name="viewport"
        content="width=device-width, initial-scale=1">
  <title>
    ${(realm.displayName)!'MeepleTime'} &#8212; Create account
  </title>
  <#if recaptchaRequired!false>
    <script
      src="https://www.google.com/recaptcha/api.js"
      async
      defer
    ></script>
  </#if>
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
        <h1 class="mt-title">Join the party</h1>
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
        id="kc-register-form"
        class="mt-form"
        action="${url.registrationAction}"
        method="post"
      >
        <div class="mt-field">
          <label for="firstName" class="mt-label">
            ${msg("firstName")}
          </label>
          <input
            id="firstName"
            class="mt-input"
            name="firstName"
            value="${(register.formData.firstName)!''}"
            type="text"
            autofocus
            autocomplete="given-name"
            aria-invalid="\
${messagesPerField.existsError('firstName')?c}"
          />
          <#if messagesPerField.existsError('firstName')>
            <span class="mt-field-error" aria-live="polite">
              ${kcSanitize(
                messagesPerField.get('firstName'))?no_esc}
            </span>
          </#if>
        </div>

        <div class="mt-field">
          <label for="lastName" class="mt-label">
            ${msg("lastName")}
          </label>
          <input
            id="lastName"
            class="mt-input"
            name="lastName"
            value="${(register.formData.lastName)!''}"
            type="text"
            autocomplete="family-name"
            aria-invalid="\
${messagesPerField.existsError('lastName')?c}"
          />
          <#if messagesPerField.existsError('lastName')>
            <span class="mt-field-error" aria-live="polite">
              ${kcSanitize(
                messagesPerField.get('lastName'))?no_esc}
            </span>
          </#if>
        </div>

        <#if !realm.registrationEmailAsUsername>
          <div class="mt-field">
            <label for="username" class="mt-label">
              ${msg("username")}
            </label>
            <input
              id="username"
              class="mt-input"
              name="username"
              value="${(register.formData.username)!''}"
              type="text"
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
        </#if>

        <div class="mt-field">
          <label for="email" class="mt-label">
            ${msg("email")}
          </label>
          <input
            id="email"
            class="mt-input"
            name="email"
            value="${(register.formData.email)!''}"
            type="email"
            autocomplete="email"
            aria-invalid="\
${messagesPerField.existsError('email')?c}"
          />
          <#if messagesPerField.existsError('email')>
            <span class="mt-field-error" aria-live="polite">
              ${kcSanitize(
                messagesPerField.get('email'))?no_esc}
            </span>
          </#if>
        </div>

        <#if passwordRequired!false>
          <div class="mt-field">
            <label for="password" class="mt-label">
              ${msg("password")}
            </label>
            <input
              id="password"
              class="mt-input"
              name="password"
              type="password"
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
        </#if>

        <#if recaptchaRequired!false>
          <div class="mt-recaptcha">
            <div
              class="g-recaptcha"
              data-size="compact"
              data-sitekey="${recaptchaSiteKey}"
            ></div>
          </div>
        </#if>

        <button class="mt-submit" name="register" type="submit">
          ${msg("doRegister")}
        </button>
      </form>

    </div>
  </div>

  <footer class="mt-footer" aria-label="Auxiliary actions">
    <div class="mt-footer-left">
      <span>${msg("alreadyHaveAnAccount")}</span>
      <a href="${url.loginUrl}">${msg("doLogIn")}</a>
    </div>
    <div class="mt-footer-right">
      <span>&#169; 2026 MeepleTime</span>
    </div>
  </footer>

</div>

</body>
</html>
