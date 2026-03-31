<#macro moduleAssets>
  <script type="importmap">
    {
      "imports": {
        "react":
          "${resourceCommonUrl}/vendor/react/react.production.min.js",
        "react/jsx-runtime":
          "${resourceCommonUrl}/vendor/react/react-jsx-runtime.production.min.js",
        "react-dom":
          "${resourceCommonUrl}/vendor/react-dom/react-dom.production.min.js"
      }
    }
  </script>

  <#if darkMode?? && darkMode>
    <script type="module" async blocking="render">
      const DARK_MODE_CLASS = "${properties.kcDarkModeClass}";
      const mediaQuery =
        window.matchMedia("(prefers-color-scheme: dark)");

      updateDarkMode(mediaQuery.matches);
      mediaQuery.addEventListener(
        "change",
        (event) => updateDarkMode(event.matches),
      );

      function updateDarkMode(isEnabled) {
        const { classList } = document.documentElement;

        if (isEnabled) {
          classList.add(DARK_MODE_CLASS);
        } else {
          classList.remove(DARK_MODE_CLASS);
        }
      }
    </script>
  </#if>

  <#if !isSecureContext>
    <script
      type="module"
      src="${resourceCommonUrl}/vendor/web-crypto-shim/web-crypto-shim.js"
    ></script>
  </#if>

  <#if devServerUrl?has_content>
    <script type="module">
      import { injectIntoGlobalHook } from
        "${devServerUrl}/@react-refresh";

      injectIntoGlobalHook(window);
      window.$RefreshReg$ = () => {};
      window.$RefreshSig$ = () => (type) => type;
    </script>
    <script type="module">
      import { inject } from
        "${devServerUrl}/@vite-plugin-checker-runtime";

      inject({
        overlayConfig: {},
        base: "/",
      });
    </script>
    <script type="module" src="${devServerUrl}/@vite/client"></script>
    <script type="module" src="${devServerUrl}/src/main.tsx"></script>
  </#if>

  <#if entryStyles?has_content>
    <#list entryStyles as style>
      <link rel="stylesheet" href="${resourceUrl}/${style}">
    </#list>
  </#if>
  <#if properties.styles?has_content>
    <#list properties.styles?split(' ') as style>
      <link rel="stylesheet" href="${resourceUrl}/${style}">
    </#list>
  </#if>

  <#if entryScript?has_content>
    <script type="module" src="${resourceUrl}/${entryScript}"></script>
  </#if>
  <#if properties.scripts?has_content>
    <#list properties.scripts?split(' ') as script>
      <script type="module" src="${resourceUrl}/${script}"></script>
    </#list>
  </#if>
  <#if entryImports?has_content>
    <#list entryImports as import>
      <link rel="modulepreload" href="${resourceUrl}/${import}">
    </#list>
  </#if>
</#macro>

<#macro loadingState>
  <main class="container">
    <div class="keycloak__loading-container">
      <svg
        class="pf-v5-c-spinner pf-m-xl"
        role="progressbar"
        aria-valuetext="Loading..."
        viewBox="0 0 100 100"
        aria-label="Contents"
      >
        <circle
          class="pf-v5-c-spinner__path"
          cx="50"
          cy="50"
          r="45"
          fill="none"
        ></circle>
      </svg>
      <div>
        <p id="loading-text">Loading your MeepleTime account</p>
      </div>
    </div>
  </main>
</#macro>

<#macro environmentScript>
  <script id="environment" type="application/json">
    {
      "serverBaseUrl": "${serverBaseUrl}",
      "authUrl": "${authUrl}",
      "authServerUrl": "${authServerUrl}",
      "realm": "${realm.name}",
      "clientId": "${clientId}",
      "resourceUrl": "${resourceUrl}",
      "logo": "${properties.logo!''}",
      "logoUrl": "${properties.logoUrl!''}",
      "baseUrl": "${baseUrl}",
      "locale": "${locale!'en'}",
      "referrerName": "${referrerName!''}",
      "referrerUrl": "${referrer_uri!''}",
      "features": {
        "isRegistrationEmailAsUsername":
          ${realm.registrationEmailAsUsername?c},
        "isEditUserNameAllowed": ${realm.editUsernameAllowed?c},
        "isInternationalizationEnabled":
          ${realm.isInternationalizationEnabled()?c},
        "isLinkedAccountsEnabled": ${isLinkedAccountsEnabled?c},
        "isMyResourcesEnabled":
          ${(realm.userManagedAccessAllowed && isAuthorizationEnabled)?c},
        "isViewOrganizationsEnabled": ${isViewOrganizationsEnabled?c},
        "deleteAccountAllowed": ${deleteAccountAllowed?c},
        "updateEmailFeatureEnabled":
          ${updateEmailFeatureEnabled?c},
        "updateEmailActionEnabled":
          ${updateEmailActionEnabled?c},
        "isViewGroupsEnabled": ${isViewGroupsEnabled?c},
        "isOid4VciEnabled": ${isOid4VciEnabled?c}
      },
      "scope": "${scope!''}"
    }
  </script>
</#macro>

<#macro page pageTitle="" pageDescription="">
  <#local mtLang = locale!'en'>
  <#local mtDir = localeDir!'ltr'>
  <!doctype html>
  <html lang="${mtLang}" dir="${mtDir}">
    <head>
      <meta charset="utf-8">
      <link
        rel="icon"
        type="${properties.favIconType!'image/svg+xml'}"
        href="${resourceUrl}${properties.favIcon!'/img/logo.svg'}"
      >
      <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
      >
      <meta
        name="color-scheme"
        content="light${(darkMode?? && darkMode)?then(' dark', '')}"
      >
      <meta name="description" content="${pageDescription}">
      <title>
        <#if pageTitle?has_content>
          ${pageTitle}
        <#else>
          ${properties.title!'MeepleTime Account'}
        </#if>
      </title>
      <@moduleAssets />
    </head>
    <body data-page-id="account">
      <#nested>
      <noscript>
        JavaScript is required to use the MeepleTime account console.
      </noscript>
      <@environmentScript />
    </body>
  </html>
</#macro>