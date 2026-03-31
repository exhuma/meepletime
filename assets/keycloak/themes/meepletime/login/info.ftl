<#import "_auth-layout.ftl" as mt>

<@mt.page>
  <@mt.messageAlert role="status" />

  <#if (client.baseUrl)?has_content>
    <@mt.submitLink
      href=(client.baseUrl)!''
      label=msg("backToApplication")
    />
  </#if>
</@mt.page>
