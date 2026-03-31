<!DOCTYPE html>
<html lang="${(locale.currentLanguageTag)!'en'}">
<head>
  <meta charset="utf-8">
  <meta name="viewport"
        content="width=device-width, initial-scale=1">
  <title>
    ${(realm.displayName)!'MeepleTime'} &#8212; Error
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
        <h1 class="mt-title">Something went wrong</h1>
      </div>

      <#if message?has_content>
        <div class="mt-alert mt-alert-error" role="alert">
          ${kcSanitize(message.summary)?no_esc}
        </div>
      </#if>

      <#if (client.baseUrl)?has_content>
        <a
          class="mt-submit"
          href="${(client.baseUrl)!''}"
          style="text-decoration:none;display:flex;"
        >
          ${msg("backToApplication")}
        </a>
      <#elseif skipLink?? && !skipLink>
        <a
          class="mt-submit"
          href="${properties.adminUrl!''}"
          style="text-decoration:none;display:flex;"
        >
          ${msg("backToApplication")}
        </a>
      </#if>

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
