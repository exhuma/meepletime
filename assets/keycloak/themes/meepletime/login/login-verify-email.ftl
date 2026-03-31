<#import "_auth-layout.ftl" as mt>

<#assign mtFooterLeft>
  <a href="${url.loginUrl}">${msg("backToLogin")}</a>
</#assign>

<#assign mtHeroSubtitle>
  We sent a verification link to
  ${(user.email)!''}.
  Click it to continue.
</#assign>

<@mt.page
  pageTitle="Verify email"
  heroTitle="Check your email"
  heroSubtitle=mtHeroSubtitle
  footerLeftHtml=mtFooterLeft
>
  <@mt.messageAlert />

  <form
    id="kc-verify-email-form"
    class="mt-form"
    action="${url.loginAction}"
    method="post"
  >
    <button class="mt-submit" type="submit">
      ${msg("doClickHere")}
    </button>
  </form>
</@mt.page>
