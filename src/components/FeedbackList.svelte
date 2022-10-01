<script>
  import FeedbackItem from "./FeedbackItem.svelte";
  export let feedback = [];
</script>

Feedback List
{#each feedback as fb (fb.id)}
  <FeedbackItem item={fb} />
{/each}