<script>
	import FeedbackForm from "./components/FeedbackForm.svelte";
	import FeedbackList from "./components/FeedbackList.svelte";
	import FeedbackStats from "./components/FeedbackStats.svelte";
	import MessagesPane from "./components/MessagesPane.svelte";
	import InputBox from "./ui/InputBox.svelte";
</script>

<header>
	Header goes here
	<!-- title of app and its stats as well as config buttons -->
</header>
<div class="flex-wrap">
	<main class="container">
		<!-- the main messages pane and bottom text entry area -->
		<!-- <FeedbackForm /> -->
		<!-- <FeedbackStats /> -->
		<MessagesPane />
		<InputBox placeholder="Write your message..." />
	</main>
	<aside>
		<!-- The connected users list -->
		aside goes here
	</aside>
</div>

<style>
	.flex-wrap {
		display: flex;
		height: 100%;
	}

	.flex-wrap > * {
		box-sizing: border-box;
		/* width: 50%; */
		padding: 10px;
	}
	.flex-wrap > main {
		height: auto;
		width: 80%;
	}
	.flex-wrap > aside {
		width: 20%;
	}
	header {
		/* float: left; */
		padding-left: 15px;
		margin-left: 15px;
	}
	aside {
		height: 100%;
		width: 30%;
		padding-left: 15px;
		margin-left: 15px;
		/* display: flexbox; */
		/* float: right; */
		font-style: italic;
		/* background-color: lightgray; */
	}
</style>
