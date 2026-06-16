Operator Guide
==============

This section covers deployment, configuration, and runbooks
for self-hosting MeepleTime.

MeepleTime expects its **identity provider (IDP) and database to be
provided externally** — it is a pure OpenID Connect resource server
and SPA, not an IDP. Start with :doc:`deployment`; the Keycloak
appendix is an optional walkthrough for operators who do not already
run an OIDC provider.

.. toctree::
   :maxdepth: 2

   deployment

.. toctree::
   :maxdepth: 2
   :caption: Appendix

   keycloak
   keycloak-theme
