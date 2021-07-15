"""
Fbook Remove Adlist
"""
import logging
import click
from rich.logging import RichHandler

from api.fbook import Fbook
from api.fbook import load_cookies

logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
log = logging.getLogger()


@click.group()
@click.pass_context
def cli(context: click.Context):
    """Main CLI function

    Load FB cookies into context

    Args:
        context (click.Context): click Context
    """
    log.info("Loading cookies from environment variable.")
    cookies = load_cookies()
    context.obj = Fbook(cookies)


@cli.command(help="Opt-out of business adlists")
@click.pass_obj
def opt_out(fb_: Fbook):
    """Opt-out of business adlist

    Args:
        fb_ (Fbook): Fbook helper obj
    """
    log.info("Loading business adlist.")
    business_adlist = fb_.get_business_adlist()
    log.info(f"Found '{len(business_adlist)}' business(es).")
    for business in business_adlist:
        name_ = business["name"]
        id_ = business["business_id"]
        status = fb_.opt_out_business(business["business_id"])
        log.info(f"Opting out business '{name_}' with id '{id_}'. Status: '{status}'.")


@cli.command(help="Remove interests")
@click.pass_obj
def rm_interest(fb_: Fbook):
    """Remove all interests

    Args:
        fb_ (Fbook): Fbook helper obj
    """
    log.info("Loading interest list.")
    interest_list = fb_.get_interest_list()
    log.info(f"Found '{len(interest_list)}' interest(s).")
    for interest in interest_list:
        name_ = interest["name"]
        id_ = interest["interest_id"]
        status = fb_.remove_interest(interest["interest_id"])
        log.info(f"Removing interest '{name_}' with id '{id_}'. Status: '{status}'.")


@cli.command(help="Delete advertisers")
@click.pass_obj
@click.option(
    "-c", "--count", type=int, default=2, help="Number of advertiser list load"
)
def del_ad(fb_: Fbook, count: int):
    """Delete advertisers

    Args:
        fb_ (Fbook): Fbook helper obj
        count (int): number of advertiser list to load
    """
    logging.info(f"Load {count} list(s) of advertisers.")

    for counter in range(count):
        log.info(f"Getting Advertisers list no {counter+1}.")
        ad_list = fb_.get_advertiser_list()
        if len(ad_list) == 0:
            log.warning("No advertiser found!")
            break

        for ad_page in ad_list:
            page_id = ad_page["advertiser_id"]
            page_name = ad_page["name"]
            status = fb_.hide_advertiser(page_id)
            log.info(f"Hiding page '{page_name}', id '{page_id}'. Hidden: '{status}'")


# Run all commands
@cli.command(name="all", help="Run all commands")
@click.pass_context
def run_all_commands(ctx):
    """Run all commands"""
    ctx.invoke(del_ad)
    ctx.invoke(opt_out)
    ctx.invoke(rm_interest)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
