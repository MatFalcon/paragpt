/** @odoo-module **/
import { Dropdown } from '@web/core/dropdown/dropdown'
import { DropdownItem } from '@web/core/dropdown/dropdown_item'
import { useService } from '@web/core/utils/hooks'
import { registry } from '@web/core/registry'
import { browser } from '@web/core/browser/browser'
import { symmetricalDifference } from "@web/core/utils/arrays";

const rpc = require('web.rpc')
const session = require('web.session');

function parseCompanyIds(cidsFromHash) {
    const cids = []
    if (typeof cidsFromHash == 'string') {
        cids.push(...cidsFromHash.split(',').map(Number))
    } else if (typeof cidsFromHash == 'number') {
        cids.push(cidsFromHash)
    }
    return cids
}

export const branchService = {
    dependencies: ['user', 'router', 'cookie'],
    start: async function(env, { user, router, cookie }) {
        let cids
        if ('cids' in router.current.hash) {
            cids = parseCompanyIds(router.current.hash.cids)
        } else if ('bchids' in cookie.current) {
            cids = parseCompanyIds(cookie.current.cids)
        } else {
            cids = []
        }

        let bchids
        if ('bchids' in router.current.hash) {
            bchids = parseCompanyIds(router.current.hash.bchids)
        } else if ('bchids' in cookie.current) {
            bchids = parseCompanyIds(cookie.current.bchids)
        } else {
            bchids = []
        }
        const allowedBranchIds = bchids

        const stringBchIds = allowedBranchIds.join(',')
        router.replaceState({ bchids: stringBchIds }, { lock: true })
        cookie.setCookie('bchids', stringBchIds)

        let availableBranches = {}
        await rpc.query({
            model: 'company_branch.company_branch',
            method: 'search_read',
            args: [[['company_id', '=', cids[0]]]],
        }).then(function(results) {
            results.forEach(branch => {
                availableBranches[branch.id] = branch
            })
            console.log('results', results)
        }).catch(function(reason){
            console.log(reason.message)
        })
        const availableBranchesIds = Object.keys(availableBranches)
        if (!bchids && availableBranchesIds) {
            bchids = availableBranchesIds[0]
            router.replaceState({ bchids: bchids }, { lock: true })
            cookie.setCookie('bchids', bchids)
        }

        return {
            availableBranches,
            get allowedBranchIds() {
                return allowedBranchIds.slice()
            },
            get currentBranch() {
                return availableBranches[allowedBranchIds[0]]
            },
            setBranches: async function(mode, ...branchIds) {
                let nextBranchIds
                if (mode === "toggle") {
                    nextBranchIds = symmetricalDifference(allowedBranchIds, branchIds);
                } else if (mode === "loginto") {
                    const branchId = branchIds[0]
                    if (allowedBranchIds.length === 1) {
                        nextBranchIds = [branchId]
                    } else {
                        nextBranchIds = [
                            branchId,
                            ...allowedBranchIds.filter((id) => id !== branchId),
                        ]
                    }
                }
                nextBranchIds = nextBranchIds.length ? nextBranchIds : [branchIds[0]]

                // apply them
                router.pushState({ bchids: nextBranchIds }, { lock: true })
                cookie.setCookie('bchids', nextBranchIds)

                user = session.uid
                await rpc.query({
                    model: 'res.users',
                    method: 'write',
                    args: [[user], {'company_branch_id': nextBranchIds[0], 'company_branch_ids': nextBranchIds}],
                }).then(function(result) {
                    console.log(result)
                    console.log('company_branch_id done')
                }).catch(function(reason){
                    console.log(reason.message)
                })

                browser.setTimeout(() => browser.location.reload()) // history.pushState is a little async
            },
        }
    },
}
registry.category('services').add('branch', branchService)

export class SwitchBranchMenu extends owl.Component {
    setup() {
        this.companyService = useService('company')
        this.branchService = useService('branch')
        this.currentCompany = this.companyService.currentCompany
        this.currentBranch = this.branchService.currentBranch
        this.state = owl.hooks.useState({ branchesToToggle: [] });
        console.log('sbm setup')
    }

    toggleBranch(branchId) {
        this.state.branchesToToggle = symmetricalDifference(this.state.branchesToToggle, [
            branchId,
        ]);
        browser.clearTimeout(this.toggleTimer);
        this.toggleTimer = browser.setTimeout(() => {
            this.branchService.setBranches("toggle", ...this.state.branchesToToggle);
        }, this.constructor.toggleDelay);
    }

    logIntoBranch(branchId) {
        this.branchService.setBranches('loginto', branchId)
    }

    get selectedBranches() {
        return symmetricalDifference(
            this.branchService.allowedBranchIds,
            this.state.branchesToToggle
        );
    }

}
SwitchBranchMenu.template = 'company_branch.SwitchBranchMenu'
SwitchBranchMenu.toggleDelay = 1000;
SwitchBranchMenu.components = { Dropdown, DropdownItem }
export const systrayItem = { Component: SwitchBranchMenu }
registry.category('systray').add('SwitchBranchMenu', systrayItem, { sequence: 0 })
