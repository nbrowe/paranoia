<script>
  import { FeedbackStore } from "../stores.js";
  import FeedbackItem from "./FeedbackItem.svelte";
  import { fade, scale } from "svelte/transition";
  import { onDestroy, onMount } from "svelte/internal";
  let feedback = [];

  // const unsubscribe = FeedbackStore.subscribe((data) => (feedback = data));


  // onMount(() => {
  //   console.log('mounted.')
  // })

  // onDestroy(() => {
  //   unsubscribe();
  // })
</script>

{#each feedback as fb (fb.id)}
  <div in:scale out:fade={{ duration: 500 }}>
    <FeedbackItem item={fb} on:delete-feedback />
  </div>
{/each}
<!-- // Reraise (event-forward) the handler up to the data store in App... -->
