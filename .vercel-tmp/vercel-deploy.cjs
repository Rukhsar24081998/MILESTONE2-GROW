#!/usr/bin/env node
/**
 * Vercel CLI Deployment Script
 * Usage: node deploy.cjs [options]
 */
const { spawnSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const isWindows = os.platform() === 'win32';

function log(msg) {
  console.error(msg);
}

function doDeploy(options) {
  log('');
  log('Starting deployment...');
  log('');
  
  const cmdParts = ['npx', 'vercel'];
  if (options.yes) cmdParts.push('--yes');
  if (options.prod) {
    cmdParts.push('--prod');
    log('Deployment environment: Production');
  }
  
  log(`Executing: ${cmdParts.join(' ')}`);
  log('');
  log('========================================');
  
  try {
    const args = cmdParts.slice(1);
    const result = spawnSync('npx', args, {
      encoding: 'utf8',
      stdio: ['inherit', 'pipe', 'pipe'],
      timeout: 300000,
      shell: isWindows
    });
    
    const output = (result.stdout || '') + (result.stderr || '');
    log(output);
    
    if (result.status !== 0) {
      throw new Error('Deployment command failed');
    }
    
    // Extract deployment URL
    const aliasedMatch = output.match(/Aliased:\s*(https:\/\/[a-zA-Z0-9.-]+\.vercel\.app)/i);
    const productionUrl = aliasedMatch ? aliasedMatch[1] : null;
    
    const deploymentMatch = output.match(/Production:\s*(https:\/\/[a-zA-Z0-9.-]+\.vercel\.app)/i);
    const deploymentUrl = deploymentMatch ? deploymentMatch[1] : null;
    
    const finalUrl = productionUrl || deploymentUrl;
    
    log('');
    log('========================================');
    log('Deployment successful!');
    log('========================================');
    log('');
    
    if (finalUrl) {
      log(`Your site is live! Visit: ${finalUrl}`);
      log('');
      console.log(JSON.stringify({ status: 'success', url: finalUrl }));
    } else {
      console.log(JSON.stringify({ status: 'success', message: 'Deployment successful' }));
    }
  } catch (error) {
    log(error.message || '');
    log('');
    log('Deployment failed');
    process.exit(1);
  }
}

function main() {
  log('========================================');
  log('Vercel CLI Project Deployment');
  log('========================================');
  log('');
  
  const options = {
    prod: true,
    yes: true
  };
  
  doDeploy(options);
}

main();
