# Money to Prisoners Common Assets

All assets used for [money-to-prisoners-cashbook](), [money-to-prisoners-prisoner-location-admin](https://github.com/ministryofjustice/money-to-prisoners-prisoner-location-admin/), [money-to-prisoners-bank-admin](https://github.com/ministryofjustice/money-to-prisoners-bank-admin/) are kept in this package.

They are included into each application using [npm](http://npmjs.com/). Each application's build scripts run npm automatically.

### Sass, Javascript, Images

Static assets are in `./assets/(images|javascripts|scss)`. The base sass file, [`_mtp.scss`](https://github.com/ministryofjustice/money-to-prisoners-common/blob/master/assets/scss/_mtp.scss), is used to include the sass includes from this packge into each frontend app.

### Django templates

Common templates used across all 3 applications are kept in `./templates/`. They are made accessible to each application by adding the path to the bower package to the template directories list in `settings.py`.

## Working with this repository locally

The applications using this repository incorporate it with npm, resulting in a of copy it in the `node_modules/money-to-prisoners-common` directory. Making modifications in that directory is possible, but since the copy doesn't include `.git` you won't be able to commit your changes.

The correct method is to clone this repo in another directory alongside this one and use npm link. Doing so will symlink the `node_modules/money-to-prisoners-common` to your local clone. Typically
```
$ git clone https://github.com/ministryofjustice/money-to-prisoners-cashbook
$ git clone https://github.com/ministryofjustice/money-to-prisoners-common
$ cd money-to-prisoners-common
$ npm link
$ cd ../money-to-prisoners-cashbook
$ npm install
$ npm link money-to-prisoners-common
```

When changes are deployed in this repo, its version should be updated and the upstream projects' `package.json` should be modified to reflect this change:
```
...
 "money-to-prisoners-common": "ministryofjustice/money-to-prisoners-common#1.2.0",
...
```

This repository has a dependency on [mojular/moj-elements](https://github.com/mojular/moj-elements), which provides the assets and scripts for MOJ sites. The [mojular](https://github.com/mojular/) repositories are shared across multiple departments, and any change should be checked by members of the organization.