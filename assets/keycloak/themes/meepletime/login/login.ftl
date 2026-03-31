<#import "_auth-layout.ftl" as mt>

<#assign mtFooterLeft = "">
<#if realm.password && realm.registrationAllowed
  && !registrationDisabled??>
  <#assign mtFooterLeft>
    <span>${msg("noAccount")}</span>
    <a href="${url.registrationUrl}">${msg("doRegister")}</a>
  </#assign>
</#if>

<@mt.page
  pageTitle="Sign in"
  heroTitle="Gather your party"
  footerLeftHtml=mtFooterLeft
>
  <@mt.messageAlert excludedFields=["username", "password"] />

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
          aria-invalid="${messagesPerField.existsError('username')?c}"
        />
        <@mt.fieldError name="username" />
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
          aria-invalid="${messagesPerField.existsError('password')?c}"
        />
        <@mt.fieldError name="password" />
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
</@mt.page>
