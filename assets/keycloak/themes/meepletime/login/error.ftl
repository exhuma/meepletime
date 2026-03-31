<#import "_auth-layout.ftl" as mt>

<@mt.page
  pageTitle="Error"
  heroTitle="Something went wrong"
>
  <@mt.messageAlert forceType="error" />

  <#if (client.baseUrl)?has_content>
    <@mt.submitLink
      href=(client.baseUrl)!''
      label=msg("backToApplication")
    />
  <#elseif skipLink?? && !skipLink>
    <@mt.submitLink
      href=(properties.adminUrl)!''
      label=msg("backToApplication")
    />
  </#if>
</@mt.page>
