<#import "_account-layout.ftl" as mt>

<#assign mtReferrerHref = "">
<#if referrer_uri?? && referrer_uri?has_content>
  <#assign mtReferrerHref = referrer_uri?replace('_hash_', '#')>
</#if>

<@mt.page
  pageTitle=(properties.title!'MeepleTime Account')
  pageDescription=(
    properties.description!
    'Manage your personal details, account security, and applications.'
  )
>
  <div class="mt-account-shell">
    <header class="mt-account-header">
      <div class="mt-account-brand-block">
        <span class="mt-account-kicker">MeepleTime account</span>
        <a class="mt-account-brand" href="${baseUrl}">
          <span class="mt-account-brand-name">MeepleTime</span>
        </a>
      </div>

      <div class="mt-account-header-copy">
        <h1 class="mt-account-title">Keep your party ready</h1>
        <p class="mt-account-subtitle">
          Manage personal info, security preferences, and linked
          applications from one branded home base.
        </p>
      </div>

      <#if mtReferrerHref?has_content>
        <a class="mt-account-return" href="${mtReferrerHref}">
          Back to ${(referrerName)!'MeepleTime'}
        </a>
      </#if>
    </header>

    <section class="mt-account-frame">
      <div class="mt-account-card">
        <div class="mt-glow" aria-hidden="true"></div>
        <div id="app" class="mt-account-console">
          <@mt.loadingState />
        </div>
      </div>
    </section>

    <footer class="mt-footer" aria-label="Contextual information">
      <div class="mt-footer-left">
        <span>OIDC account management via Keycloak</span>
      </div>
      <div class="mt-footer-right">
        <span>&#169; 2026 MeepleTime</span>
      </div>
    </footer>
  </div>
</@mt.page>