# Money to Prisoners Common Assets

All assets used for [money-to-prisoners-cashbook](), [money-to-prisoners-prisoner-location-admin](https://github.com/ministryofjustice/money-to-prisoners-prisoner-location-admin/), [money-to-prisoners-bank-admin](https://github.com/ministryofjustice/money-to-prisoners-bank-admin/) are kept in this package.

They are included into each application using [Bower](http://bower.io/).

### Sass, Javascript, Images

Static assets are in `./assets/(images|javascripts|scss)`. The base sass file, [`_mtp.scss`](https://github.com/ministryofjustice/money-to-prisoners-common/blob/master/assets/scss/_mtp.scss), is used to include the sass includes from this packge into each frontend app.

### Gulp

The majority of the [Gulp](http://gulpjs.com/) tasks remain the same for each app so have been included in this package. 

They are then copied into a common tasks folder in each application, `./tasks/common/`, so they can be accessed through the application gulpfile. This process is handled by a Bower [postinstall hook](https://github.com/bower/bower/blob/master/HOOKS.md). These tasks are kept in `./tasks/`

### Django templates

Common templates used across all 3 applications are kept in `./templates/`. They are made accessible to each application by adding the path to the bower package to the template directories list in `settings.py`.

## Working with this repository locally

You can utilise [bower link](http://bower.io/docs/api/#link) to point the application that includes this package to a local copy so that changes are picked up immediately. Once all your changes are complete you can combine this in a series of commits or Pull Request. 

*Note:* Gulp tasks are copied into the application's `./tasks/common/` directory using a bower [postinstall hook](https://github.com/bower/bower/blob/master/HOOKS.md), however, this is not trigured after a bower link. 

If you make changes to the tasks and need them in the application you can run the command bower is running in that repository after an install.
