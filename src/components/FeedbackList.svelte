<script>
  import FeedbackItem from "./FeedbackItem.svelte";
  export let feedback = [];
</script>

Feedback List
{#each feedback as fb (fb.id)}
  <FeedbackItem item={fb} on:delete-feedback />
{/each}
<!-- // Reraise (event-forward) the handler up to the data store in App... -->