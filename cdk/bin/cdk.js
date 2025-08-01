const cdk = require('aws-cdk-lib');
const path = require('path');

require('dotenv').config({ path: path.resolve(__dirname, '../../.env') });

const { CustomerAgentStack } = require('../lib/cdk-stack');

const app = new cdk.App();

new CustomerAgentStack (app, 'CustomerAgentStack', {
  /* If you don't specify 'env', this stack will be environment-agnostic.
   * Account/Region-dependent features and context lookups will not work,
   * but a single synthesized template can be deployed anywhere. */

  /* Uncomment the next line if you know exactly what Account and Region you
   * want to deploy the stack to. */
  env: { account: process.env.AWS_ACCOUNT_ID, region: process.env.AWS_REGION  },

  /* For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html */
});
