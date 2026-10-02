/*
 * Application entry point: imports Bootstrap CSS and mounts the root
 * Svelte component. Scope: bootstrap only. Limitations: none.
 */
import 'bootstrap/dist/css/bootstrap.min.css'
import { mount } from 'svelte'
import App from './App.svelte'

export default mount(App, { target: document.getElementById('app') })
