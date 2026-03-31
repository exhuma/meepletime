<#import "_auth-layout.ftl" as mt>

<#assign mtFooterLeft>
  <a href="${url.loginUrl}">${msg("backToLogin")}</a>
</#assign>

<@mt.page
  pageTitle="Reset password"
  heroTitle="Forgot your password?"
  heroSubtitle="Enter your address and we&#8217;ll send a link."
  footerLeftHtml=mtFooterLeft
>
  <@mt.messageAlert />

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
        aria-invalid="${messagesPerField.existsError('username')?c}"
      />
      <@mt.fieldError name="username" />
    </div>

    <button class="mt-submit" type="submit">
      ${msg("doSubmit")}
    </button>
  </form>
</@mt.page>
