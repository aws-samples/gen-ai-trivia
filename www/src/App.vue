<script setup>
  import { Authenticator } from "@aws-amplify/ui-vue";
  import "@aws-amplify/ui-vue/styles.css";
  import { Amplify } from 'aws-amplify';
  import config from './amplifyconfiguration.json';
  Amplify.configure(config);
</script>

<template>
  <authenticator>
    <template v-slot="{ user, signOut }">
      <div class="container">
        <router-view></router-view>
      </div>
    </template>
  </authenticator>
</template>
