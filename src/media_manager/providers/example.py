"""
Example usage of provider clients.

This module demonstrates how to use the TMDB and TheTVDB providers
with fuzzy search to find media information from filenames.
"""

from media_manager.providers import MediaSearcher, TheTVDBClient, TMDBClient
from media_manager.settings import SettingsManager


async def example_usage() -> None:
    """Example of using provider clients."""

    # Initialize settings
    settings = SettingsManager()

    # Set API keys (in a real app, these would be configured by the user)
    settings.set_tmdb_api_key("your_tmdb_api_key_here")
    settings.set_thetvdb_api_key("your_thetvdb_api_key_here")

    # Create provider clients
    tmdb_client = TMDBClient(settings)
    thetvdb_client = TheTVDBClient(settings)

    # Create media searcher with both providers
    providers = {
        "tmdb": tmdb_client,
        "thetvdb": thetvdb_client
    }
    searcher = MediaSearcher(providers)

    # Example filenames to search for
    filenames = [
        "Fight.Club.1999.1080p.BluRay.x264-GROUP",
        "Breaking.Bad.S01E01.2008.1080p.WEB-DL.x264-GROUP",
        "The.Matrix.1999.1080p.BluRay.x264-GROUP",
        "Game.of.Thrones.S08E06.2019.1080p.HDTV.x264-GROUP"
    ]

    print("Media Search Example")
    print("=" * 50)

    for filename in filenames:
        print(f"\nSearching for: {filename}")
        print("-" * 30)

        try:
            # Search by filename
            results = await searcher.search_by_filename(filename, providers=["tmdb"])

            if results:
                for i, result in enumerate(results[:3], 1):  # Show top 3 results
                    print(f"{i}. {result.item.title} (Score: {result.score:.1f})")
                    print(f"   Provider: {result.provider}")
                    print(f"   Type: {result.media_type.value}")

                    if hasattr(result.item, 'release_date') and result.item.release_date:
                        print(f"   Year: {result.item.release_date.year}")
                    if hasattr(result.item, 'first_air_date') and result.item.first_air_date:
                        print(f"   Year: {result.item.first_air_date.year}")
            else:
                print("No results found")

        except Exception as e:
            print(f"Error: {e}")

    # Example of direct search
    print("\n\nDirect Search Example")
    print("=" * 50)

    try:
        # Search for movies directly
        movie_results = await searcher.search_by_query("Inception", MediaType.MOVIE, providers=["tmdb"])
        print(f"\nFound {len(movie_results)} movies matching 'Inception':")
        for result in movie_results[:3]:
            year = result.item.release_date.year if hasattr(result.item, 'release_date') and result.item.release_date else 'N/A'
            print(f"- {result.item.title} ({year})")

        # Search for TV shows directly
        tv_results = await searcher.search_by_query("Stranger Things", MediaType.TV_SHOW, providers=["tmdb"])
        print(f"\nFound {len(tv_results)} TV shows matching 'Stranger Things':")
        for result in tv_results[:3]:
            year = result.item.first_air_date.year if hasattr(result.item, 'first_air_date') and result.item.first_air_date else 'N/A'
            print(f"- {result.item.title} ({year})")

    except Exception as e:
        print(f"Error in direct search: {e}")

    # Clean up
    await tmdb_client.close()
    await thetvdb_client.close()


if __name__ == "__main__":
    # Note: This example requires actual API keys to work
    # It's intended to show the API usage pattern
    print("This is an example demonstrating the provider client usage.")
    print("To run this example, you need to:")
    print("1. Get API keys from TMDB and TheTVDB")
    print("2. Set them in the settings")
    print("3. Run: python -m media_manager.providers.example")

    # Uncomment the following lines and add your API keys to test:
    # asyncio.run(example_usage())
