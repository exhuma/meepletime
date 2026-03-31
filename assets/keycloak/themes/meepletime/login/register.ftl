<#import "_auth-layout.ftl" as mt>

<#assign mtExtraHead = "">
<#if recaptchaRequired!false>
  <#assign mtExtraHead>
    <script
      src="https://www.google.com/recaptcha/api.js"
      async
      defer
    ></script>
  </#assign>
</#if>

<#assign mtFooterLeft>
  <span>${msg("alreadyHaveAnAccount")}</span>
  <a href="${url.loginUrl}">${msg("doLogIn")}</a>
</#assign>

<@mt.page
  pageTitle="Create account"
  heroTitle="Join the party"
  footerLeftHtml=mtFooterLeft
  extraHeadHtml=mtExtraHead
>
  <@mt.messageAlert />

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
        aria-invalid="${messagesPerField.existsError('firstName')?c}"
      />
      <@mt.fieldError name="firstName" />
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
        aria-invalid="${messagesPerField.existsError('lastName')?c}"
      />
      <@mt.fieldError name="lastName" />
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
          aria-invalid="${messagesPerField.existsError('username')?c}"
        />
        <@mt.fieldError name="username" />
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
        aria-invalid="${messagesPerField.existsError('email')?c}"
      />
      <@mt.fieldError name="email" />
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
          aria-invalid="${messagesPerField.existsError('password')?c}"
        />
        <@mt.fieldError name="password" />
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
          aria-invalid="${messagesPerField.existsError('password-confirm')?c}"
        />
        <@mt.fieldError name="password-confirm" />
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
</@mt.page>
