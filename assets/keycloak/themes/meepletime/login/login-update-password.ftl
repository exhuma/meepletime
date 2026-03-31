<#import "_auth-layout.ftl" as mt>

<@mt.page
  pageTitle="New password"
  heroTitle="Set your new password"
>
  <@mt.messageAlert
    excludedFields=["password", "password-confirm"]
  />

  <form
    id="kc-passwd-update-form"
    class="mt-form"
    action="${url.loginAction}"
    method="post"
  >
    <input
      type="text"
      id="username"
      name="username"
      value="${(username)!''}"
      autocomplete="username"
      readonly
      hidden
    />
    <input
      type="password"
      id="password-new"
      name="password-new"
      autocomplete="new-password"
      hidden
    />

    <div class="mt-field">
      <label for="password" class="mt-label">
        ${msg("passwordNew")}
      </label>
      <input
        id="password"
        class="mt-input"
        name="password"
        type="password"
        autofocus
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

    <button class="mt-submit" type="submit">
      ${msg("doSubmit")}
    </button>
  </form>
</@mt.page>
