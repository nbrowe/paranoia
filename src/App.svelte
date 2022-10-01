<script>
	import FeedbackForm from "./components/FeedbackForm.svelte";
	import FeedbackList from "./components/FeedbackList.svelte";
	import FeedbackStats from "./components/FeedbackStats.svelte";

	let feedback = [
		{
			id: 1,
			rating: 10,
			text: "dummy value",
		},
	];

	// reactive values
	$: count = feedback.length;
	$: average =
		feedback.reduce((prev, { rating }) => prev + rating, 0) / feedback.length;

	const deleteFeedback = (e) => {
		const itemId = e.detail;
		feedback = feedback.filter((item) => item.id != itemId);
	};

	const addFeedback = (e) => {
		const newFeedbackItem = e.detail;
		feedback = [...feedback, newFeedbackItem];
	}
</script>

<main class="container">
	<FeedbackForm on:submit-feedback={addFeedback}/>
	<FeedbackStats {count} {average} />
	<FeedbackList on:delete-feedback={deleteFeedback} />
</main>
